import json
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.request import ClaimVerifyRequest
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_claim_verification_task
from app.security.rate_limiter import rate_limit_dependency
from app.security.authentication import require_authenticated_user, get_user_id_from_token, TokenData

router = APIRouter(tags=["Claim Verification"])


@router.post("/verify/claim", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_claim_endpoint(
    request: ClaimVerifyRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Submits a textual claim for factual verification."""
    job_repo = JobRepository(db)
    user_id = get_user_id_from_token(token_data, db)
    input_meta = json.dumps({"claim_text": request.claim_text, "context": request.context})
    job = job_repo.create_job(job_type="claim", input_data=input_meta, user_id=user_id)

    background_tasks.add_task(
        run_claim_verification_task,
        job.id,
        request.claim_text,
        request.context
    )

    return job
