import os
import uuid
from pathlib import Path
from typing import Tuple, Set
from fastapi import HTTPException, UploadFile, status

from app.config import settings

# Recognized magic byte signatures
MAGIC_SIGNATURES = {
    # Images
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "riff_based",  # WebP or WAV - inspect further
    # Video
    b"\x00\x00\x00\x18ftyp": "video/mp4",
    b"\x00\x00\x00\x1cftyp": "video/mp4",
    b"\x00\x00\x00\x20ftyp": "video/mp4",
    b"\x1a\x45\xdf\xa3": "video/webm",
    # Audio
    b"ID3": "audio/mp3",
    b"\xff\xfb": "audio/mp3",
    b"\xff\xf3": "audio/mp3",
    b"\xff\xf2": "audio/mp3",
    b"OggS": "audio/ogg",
}


def sanitize_filename(original_filename: str) -> str:
    """Strip dangerous characters and path traversal components."""
    clean_name = os.path.basename(original_filename or "unnamed_file")
    # Allow alphanumeric, underscore, hyphen, and period
    sanitized = "".join(c for c in clean_name if c.isalnum() or c in (".", "_", "-")).strip()
    return sanitized or "file"


def validate_file_size(file_bytes: bytes, max_mb: int, file_category: str) -> None:
    max_bytes = max_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{file_category} exceeds the maximum allowed size of {max_mb}MB (Received {len(file_bytes) / (1024*1024):.1f}MB)."
        )
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )


def inspect_magic_bytes(header: bytes) -> str:
    """Identify mime type from initial bytes."""
    for sig, mime in MAGIC_SIGNATURES.items():
        if header.startswith(sig):
            if sig == b"RIFF":
                if len(header) >= 12:
                    riff_type = header[8:12]
                    if riff_type == b"WEBP":
                        return "image/webp"
                    elif riff_type == b"WAVE":
                        return "audio/wav"
                return "application/octet-stream"
            return mime
    # Check for general ISO Base Media File Format (MP4 / MOV)
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "video/mp4"
    return "application/octet-stream"


async def save_and_validate_upload(
    upload_file: UploadFile,
    category: str,
    allowed_extensions: Set[str],
    max_mb: int
) -> Tuple[Path, str, int]:
    """
    Safely reads, validates signatures, generates collision-proof path,
    and stores to disk. Returns (file_path, detected_mime, file_size).
    """
    original_name = sanitize_filename(upload_file.filename or "")
    ext = os.path.splitext(original_name)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions for {category}: {', '.join(allowed_extensions)}"
        )

    content = await upload_file.read()
    validate_file_size(content, max_mb, category.capitalize())

    # Validate header signature
    header = content[:32]
    detected_mime = inspect_magic_bytes(header)

    # Basic signature matching
    valid_mime = False
    if category == "image" and (detected_mime.startswith("image/") or detected_mime == "application/octet-stream"):
        valid_mime = True
    elif category == "video" and (detected_mime.startswith("video/") or ext in settings.ALLOWED_VIDEO_EXTENSIONS):
        valid_mime = True
    elif category == "audio" and (detected_mime.startswith("audio/") or ext in settings.ALLOWED_AUDIO_EXTENSIONS):
        valid_mime = True

    if not valid_mime and detected_mime != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File content does not match expected {category} format (detected: {detected_mime})."
        )

    # Generate isolated random storage path
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    target_path = settings.UPLOAD_DIR / unique_filename

    # Ensure no directory traversal outside UPLOAD_DIR
    resolved = target_path.resolve()
    if not str(resolved).startswith(str(settings.UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid destination path.")

    with open(target_path, "wb") as f:
        f.write(content)

    return target_path, detected_mime, len(content)
