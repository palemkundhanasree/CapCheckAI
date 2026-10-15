from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class MediaMetadataSchema(BaseModel):
    filename: str
    file_size_bytes: int
    mime_type: str
    dimensions: Optional[str] = None
    duration_seconds: Optional[float] = None
    exif: Dict[str, Any] = {}
    software: Optional[str] = None
    camera_model: Optional[str] = None
    has_c2pa: bool = False
    c2pa_issuer: Optional[str] = None


class MediaUploadResponse(BaseModel):
    file_id: str
    original_name: str
    mime_type: str
    file_size: int
    path: str
