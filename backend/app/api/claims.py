import json
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.request import ClaimVerifyRequest
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_claim_verification_task
from app.security.rate_limiter import rate_limit_dependency
from app.security.authentication import require_user, TokenData

router = APIRouter(tags=["Claim Verification"])


@router.post("/verify/claim", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_claim_endpoint(
    request: ClaimVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_user)
):
    """Submits a textual claim for factual verification."""
    job_repo = JobRepository(db)
    input_meta = json.dumps({"claim_text": request.claim_text, "context": request.context})
    job = job_repo.create_job(job_type="claim", input_data=input_meta, user_id=user.uid)

    background_tasks.add_task(
        run_claim_verification_task,
        job.id,
        request.claim_text,
        request.context
    )

    return job
