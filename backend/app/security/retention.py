import os
import time
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


def cleanup_expired_files(max_age_hours: int = 48) -> int:
    """
    Scans temporary and upload directories, removing files older than max_age_hours.
    Returns the count of purged files.
    """
    cutoff = time.time() - (max_age_hours * 3600)
    purged_count = 0

    scan_directories = [settings.TEMP_DIR, settings.UPLOAD_DIR]

    for directory in scan_directories:
        if not directory.exists():
            continue
        try:
            for item in directory.iterdir():
                if item.is_file():
                    try:
                        mtime = item.stat().st_mtime
                        if mtime < cutoff:
                            item.unlink(missing_ok=True)
                            purged_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete expired file {item}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory} for cleanup: {e}")

    logger.info(f"Retention cleaner purged {purged_count} files older than {max_age_hours}h.")
    return purged_count


def delete_associated_files(file_paths: list[str]) -> None:
    """Safely deletes specific files referenced by a deleted report/job."""
    for path_str in file_paths:
        if not path_str:
            continue
        try:
            p = Path(path_str).resolve()
            # Security safeguard: ensure file is strictly inside STORAGE_DIR
            if str(p).startswith(str(settings.STORAGE_DIR.resolve())):
                if p.exists() and p.is_file():
                    p.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not remove file {path_str}: {e}")
