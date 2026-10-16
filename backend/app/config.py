import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
STORAGE_DIR = ROOT_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
REPORT_DIR = STORAGE_DIR / "reports"
TEMP_DIR = STORAGE_DIR / "temp"

# Ensure storage directories exist
for directory in [STORAGE_DIR, UPLOAD_DIR, REPORT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "CapCheck AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Storage Paths
    STORAGE_DIR: Path = STORAGE_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    REPORT_DIR: Path = REPORT_DIR
    TEMP_DIR: Path = TEMP_DIR

    # Demo Mode: if True, enables realistic simulated verification datasets alongside live APIs
    DEMO_MODE: bool = True

    # Security & CORS
    SECRET_KEY: str = "capcheck-ai-insecure-default-change-in-production-7f89d31b"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    # Database
    DATABASE_URL: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.strip() == "*":
                self.CORS_ORIGINS = ["*"]
            else:
                self.CORS_ORIGINS = [orig.strip() for orig in self.CORS_ORIGINS.split(",") if orig.strip()]
        if not self.DATABASE_URL or "storage/capcheck.db" in self.DATABASE_URL or self.DATABASE_URL.startswith("sqlite:///./"):
            db_abs = (STORAGE_DIR / "capcheck.db").resolve().as_posix()
            self.DATABASE_URL = f"sqlite:///{db_abs}"
        elif self.DATABASE_URL.startswith("sqlite:///") and not self.DATABASE_URL.startswith("sqlite:////") and ":" not in self.DATABASE_URL[10:13]:
            # Relative path provided
            rel_part = self.DATABASE_URL.replace("sqlite:///", "")
            db_abs = (ROOT_DIR / rel_part).resolve().as_posix()
            self.DATABASE_URL = f"sqlite:///{db_abs}"

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    BURST_LIMIT: int = 20

    # File Upload Limits
    MAX_IMAGE_SIZE_MB: int = 25
    MAX_VIDEO_SIZE_MB: int = 150
    MAX_AUDIO_SIZE_MB: int = 50
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".mov", ".webm", ".avi"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".m4a", ".ogg"]

    # External Provider Keys (Optional)
    GOOGLE_FACTCHECK_API_KEY: str = ""
    BING_SEARCH_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""

    # Retention Policy
    RETENTION_HOURS: int = 48  # Auto-cleanup temporary uploads older than 48 hours

    class Config:
        env_file = ROOT_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
