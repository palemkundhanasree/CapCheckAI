import json
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.request import UrlVerifyRequest
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_url_verification_task
from app.security.url_safety import validate_url_safety
from app.security.rate_limiter import rate_limit_dependency
from app.security.authentication import require_user, TokenData

router = APIRouter(tags=["URL Article Verification"])


@router.post("/verify/url", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_url_endpoint(
    request: UrlVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_user)
):
    """Submits a news article or web URL for claim extraction and verification."""
    # Pre-validate URL for SSRF safety before accepting
    safe_url = validate_url_safety(request.url)

    job_repo = JobRepository(db)
    input_meta = json.dumps({"url": safe_url})
    job = job_repo.create_job(job_type="url", input_data=input_meta, user_id=user.uid)

    background_tasks.add_task(
        run_url_verification_task,
        job.id,
        safe_url
    )

    return job
