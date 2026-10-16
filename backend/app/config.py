import os
import sys
import shutil
import sqlite3
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
STORAGE_DIR = ROOT_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
REPORT_DIR = STORAGE_DIR / "reports"
TEMP_DIR = STORAGE_DIR / "temp"

# Ensure storage directories exist in ROOT_DIR
for directory in [STORAGE_DIR, UPLOAD_DIR, REPORT_DIR, TEMP_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Fallback: also ensure backend/storage directories exist so relative path references in backend never fail
for directory in [BASE_DIR / "storage", BASE_DIR / "storage" / "uploads", BASE_DIR / "storage" / "reports", BASE_DIR / "storage" / "temp"]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _local_db_dir() -> Path:
    """A per-user folder that is NOT synced by OneDrive/Dropbox (SQLite breaks on synced folders)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME") or str(Path.home())
    d = Path(base) / "CapCheck"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sqlite_can_open(path: Path) -> bool:
    """True if SQLite can really create/write the DB file (and its journal) at this path."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=5)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS _truthlens_probe (id INTEGER)")
            conn.execute("DROP TABLE IF EXISTS _truthlens_probe")
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def _is_synced_folder(path: Path) -> bool:
    return any(part.lower().startswith(("onedrive", "dropbox", "google drive")) for part in path.parts)


def _pick_sqlite_path(p: Path) -> Path:
    """Return a SQLite path that is guaranteed to open. Falls back to a local, non-synced folder."""
    if not _is_synced_folder(p) and _sqlite_can_open(p):
        return p
    try:
        fallback = _local_db_dir() / p.name
        if not fallback.exists() and p.exists():
            try:
                shutil.copy2(p, fallback)  # keep existing users/reports
            except Exception:
                pass
        if _sqlite_can_open(fallback):
            print(f"[CapCheck] Using local database: {fallback}", file=sys.stderr)
            return fallback
    except Exception:
        pass
    return p


def normalize_database_url(url: str) -> str:
    """Ensures SQLite URLs resolve to absolute paths and directories exist regardless of CWD."""
    if not url or not str(url).strip():
        db_file = _pick_sqlite_path((STORAGE_DIR / "capcheck.db").resolve())
        return f"sqlite:///{db_file.as_posix()}"

    url = str(url).strip()
    if url.startswith("sqlite:"):
        if ":memory:" in url:
            return url
        if url.startswith("sqlite:////"):
            raw_path = "/" + url[len("sqlite:////"):]
        elif url.startswith("sqlite:///"):
            raw_path = url[len("sqlite:///"): ]
        elif url.startswith("sqlite://"):
            raw_path = url[len("sqlite://"): ]
        else:
            raw_path = url[len("sqlite:"): ]

        p = Path(raw_path)
        if not p.is_absolute():
            p = (ROOT_DIR / p).resolve()
        else:
            p = p.resolve()

        p = _pick_sqlite_path(p)
        return f"sqlite:///{p.as_posix()}"

    return url


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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    # Database
    DATABASE_URL: str = f"sqlite:///{(STORAGE_DIR / 'capcheck.db').resolve().as_posix()}"

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
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""

    # Google Gemini (AI fact-check of text claims)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_GROUNDING: bool = True  # let Gemini use Google Search for up-to-date facts

    # Email (SMTP) used for password-reset and email sign-in codes
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_SSL: bool = False  # True for port 465
    # Local development only: return the one-time code in the API response when SMTP is not configured
    EXPOSE_DEV_OTP: bool = False
    OTP_TTL_MINUTES: int = 10

    # Retention Policy
    RETENTION_HOURS: int = 48  # Auto-cleanup temporary uploads older than 48 hours

    class Config:
        env_file = ROOT_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
# Ensure settings.DATABASE_URL is always absolute and storage directory exists
try:
    settings.DATABASE_URL = normalize_database_url(settings.DATABASE_URL)
except Exception:
    pass
