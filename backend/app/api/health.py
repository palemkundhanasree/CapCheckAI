import sys
import platform
import importlib.util
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """System health status, version, and engine availability."""
    opencv_ok = importlib.util.find_spec("cv2") is not None
    whisper_ok = importlib.util.find_spec("whisper") is not None

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "production" if not settings.DEBUG else "development",
        "demo_mode": settings.DEMO_MODE,
        "system": {
            "python_version": sys.version.split()[0],
            "os": platform.system(),
            "platform": platform.platform(),
            "opencv_available": opencv_ok,
            "whisper_available": whisper_ok,
            "google_factcheck_configured": bool(settings.GOOGLE_FACTCHECK_API_KEY)
        }
    }
