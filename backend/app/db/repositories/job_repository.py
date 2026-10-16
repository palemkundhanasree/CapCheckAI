from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import VerificationJob


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_type: str, input_data: str = "", user_id: Optional[str] = None) -> VerificationJob:
        job = VerificationJob(
            job_type=job_type,
            status="queued",
            progress=0,
            current_stage="Job received and queued",
            input_data=input_data,
            user_id=user_id
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job_by_id(self, job_id: str) -> Optional[VerificationJob]:
        return self.db.query(VerificationJob).filter(VerificationJob.id == job_id).first()

    def update_progress(self, job_id: str, progress: int, stage: str) -> Optional[VerificationJob]:
        job = self.get_job_by_id(job_id)
        if job:
            job.status = "processing"
            job.progress = progress
            job.current_stage = stage
            job.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def complete_job(self, job_id: str, report_id: str) -> Optional[VerificationJob]:
        job = self.get_job_by_id(job_id)
        if job:
            job.status = "completed"
            job.progress = 100
            job.current_stage = "Analysis complete"
            job.report_id = report_id
            job.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def fail_job(self, job_id: str, error_message: str) -> Optional[VerificationJob]:
        job = self.get_job_by_id(job_id)
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.current_stage = f"Failed: {error_message}"
            job.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def get_recent_jobs(self, limit: int = 50, user_id: Optional[str] = None) -> List[VerificationJob]:
        q = self.db.query(VerificationJob)
        if user_id:
            q = q.filter(VerificationJob.user_id == user_id)
        return q.order_by(VerificationJob.created_at.desc()).limit(limit).all()
