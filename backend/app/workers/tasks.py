import logging
from pathlib import Path
from typing import Optional
from app.db.session import SessionLocal
from app.services.orchestrator import VerificationOrchestrator

logger = logging.getLogger(__name__)


async def run_claim_verification_task(job_id: str, claim_text: str, context: Optional[str] = None):
    db = SessionLocal()
    try:
        orchestrator = VerificationOrchestrator(db)
        await orchestrator.verify_claim(job_id, claim_text, context)
    except Exception as e:
        logger.error(f"Background task claim error: {e}")
    finally:
        db.close()


async def run_url_verification_task(job_id: str, url: str):
    db = SessionLocal()
    try:
        orchestrator = VerificationOrchestrator(db)
        await orchestrator.verify_url(job_id, url)
    except Exception as e:
        logger.error(f"Background task URL error: {e}")
    finally:
        db.close()


async def run_image_verification_task(job_id: str, file_path_str: str, user_context: Optional[str] = None):
    db = SessionLocal()
    try:
        orchestrator = VerificationOrchestrator(db)
        await orchestrator.verify_image(job_id, Path(file_path_str), user_context)
    except Exception as e:
        logger.error(f"Background task image error: {e}")
    finally:
        db.close()


async def run_audio_verification_task(job_id: str, file_path_str: str):
    db = SessionLocal()
    try:
        orchestrator = VerificationOrchestrator(db)
        await orchestrator.verify_audio(job_id, Path(file_path_str))
    except Exception as e:
        logger.error(f"Background task audio error: {e}")
    finally:
        db.close()


async def run_video_verification_task(job_id: str, file_path_str: str):
    db = SessionLocal()
    try:
        orchestrator = VerificationOrchestrator(db)
        await orchestrator.verify_video(job_id, Path(file_path_str))
    except Exception as e:
        logger.error(f"Background task video error: {e}")
    finally:
        db.close()
