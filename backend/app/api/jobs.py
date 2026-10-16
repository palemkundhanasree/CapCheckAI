from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.report import JobStatusResponse, JobListResponse
from app.security.authentication import require_user, can_access, TokenData

router = APIRouter(tags=["Jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Retrieves processing progress for one of the signed-in user's jobs."""
    job = JobRepository(db).get_job_by_id(job_id)
    if not job or not can_access(job.user_id, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification job not found.")
    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_recent_jobs(limit: int = 20, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Lists the signed-in user's recent verification jobs."""
    jobs = JobRepository(db).get_recent_jobs(limit=min(limit, 100), user_id=user.uid)
    return JobListResponse(total=len(jobs), jobs=jobs)
