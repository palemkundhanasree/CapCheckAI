import json
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.request import UrlVerifyRequest
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_url_verification_task
from app.security.url_safety import validate_url_safety
from app.security.rate_limiter import rate_limit_dependency
from app.security.authentication import require_authenticated_user, get_user_id_from_token, TokenData

router = APIRouter(tags=["URL Article Verification"])


@router.post("/verify/url", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_url_endpoint(
    request: UrlVerifyRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    clean_url = (request.url or "").strip()
    if not clean_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a valid article or website URL.")

    # Normalize URL format
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        safe_url = validate_url_safety(clean_url)
    except HTTPException:
        safe_url = clean_url

    job_repo = JobRepository(db)
    user_id = get_user_id_from_token(token_data, db)
    input_meta = json.dumps({"url": safe_url})
    job = job_repo.create_job(job_type="url", input_data=input_meta, user_id=user_id)

    background_tasks.add_task(
        run_url_verification_task,
        job.id,
        safe_url
    )

    return job
