import json
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.repositories.job_repository import JobRepository
from app.schemas.report import JobStatusResponse
from app.workers.tasks import run_audio_verification_task
from app.security.file_validation import save_and_validate_upload
from app.security.rate_limiter import rate_limit_dependency
from app.security.authentication import require_user, TokenData

router = APIRouter(tags=["Audio Forensics"])


@router.post("/verify/audio", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_dependency)])
async def verify_audio_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_user)
):
    """Uploads audio for synthetic speech detection, voice cloning analysis, and spoken claim verification."""
    saved_path, detected_mime, file_size = await save_and_validate_upload(
        upload_file=file,
        category="audio",
        allowed_extensions=set(settings.ALLOWED_AUDIO_EXTENSIONS),
        max_mb=settings.MAX_AUDIO_SIZE_MB
    )

    job_repo = JobRepository(db)
    input_meta = json.dumps({
        "original_name": file.filename,
        "saved_path": str(saved_path),
        "file_size": file_size
    })
    job = job_repo.create_job(job_type="audio", input_data=input_meta, user_id=user.uid)

    background_tasks.add_task(
        run_audio_verification_task,
        job.id,
        str(saved_path)
    )

    return job
