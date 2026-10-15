import json
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_video_verification_task
from app.security.file_validation import save_and_validate_upload
from app.security.rate_limiter import rate_limit_dependency

router = APIRouter(tags=["Video Forensics"])


@router.post("/verify/video", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_video_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploads a video for frame extraction, deepfake detection, temporal jitter analysis, and audio check."""
    saved_path, detected_mime, file_size = await save_and_validate_upload(
        upload_file=file,
        category="video",
        allowed_extensions=set(settings.ALLOWED_VIDEO_EXTENSIONS),
        max_mb=settings.MAX_VIDEO_SIZE_MB
    )

    job_repo = JobRepository(db)
    input_meta = json.dumps({
        "original_name": file.filename,
        "saved_path": str(saved_path),
        "file_size": file_size
    })
    job = job_repo.create_job(job_type="video", input_data=input_meta)

    background_tasks.add_task(
        run_video_verification_task,
        job.id,
        str(saved_path)
    )

    return job
