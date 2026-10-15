from pathlib import Path
from typing import Dict, Any
from fastapi import HTTPException, status
from app.config import settings


def validate_video_file(file_path: Path) -> Dict[str, Any]:
    """
    Validates video file presence, extension, and size limits.
    """
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found.")

    ext = file_path.suffix.lower()
    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )

    size = file_path.stat().st_size
    max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video exceeds limit of {settings.MAX_VIDEO_SIZE_MB}MB."
        )

    return {
        "format": ext.replace(".", "").upper(),
        "file_size_bytes": size,
        "is_valid": True
    }
