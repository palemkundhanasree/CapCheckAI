from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.report import JobStatusResponse, JobListResponse

router = APIRouter(tags=["Jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Retrieves current processing progress and report link for a given job."""
    job_repo = JobRepository(db)
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification job not found.")
    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_recent_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """Lists recent verification jobs."""
    job_repo = JobRepository(db)
    jobs = job_repo.get_recent_jobs(limit=limit)
    return JobListResponse(total=len(jobs), jobs=jobs)
