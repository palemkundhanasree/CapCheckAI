from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.report import JobStatusResponse, JobListResponse
from app.security.authentication import get_current_user_optional, require_authenticated_user, get_user_id_from_token, TokenData

router = APIRouter(tags=["Jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieves current processing progress and report link for a given job."""
    job_repo = JobRepository(db)
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification job not found.")

    if job.user_id:
        current_uid = get_user_id_from_token(token_data, db)
        is_admin = token_data and token_data.role == "admin"
        if not is_admin and job.user_id != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This verification job belongs to another user account."
            )

    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_recent_jobs(
    limit: int = 20,
    all_users: bool = False,
    token_data: TokenData = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Lists recent verification jobs for the authenticated user only."""
    user_id = get_user_id_from_token(token_data, db)
    job_repo = JobRepository(db)
    if all_users and token_data.role == "admin":
        jobs = job_repo.get_recent_jobs(limit=limit, include_all=True)
    else:
        jobs = job_repo.get_recent_jobs(limit=limit, user_id=user_id)
    return JobListResponse(total=len(jobs), jobs=jobs)
