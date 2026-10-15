import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, ROOT_DIR
from app.db.session import init_db
from app.security.retention import cleanup_expired_files

# API Routers
from app.api.health import router as health_router
from app.api.claims import router as claims_router
from app.api.news import router as news_router
from app.api.images import router as images_router
from app.api.videos import router as videos_router
from app.api.audio import router as audio_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.history import router as history_router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("truthlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite DB schema and run retention sweep
    logger.info("Initializing TruthLens AI backend...")
    init_db()
    cleanup_expired_files(settings.RETENTION_HOURS)
    yield
    # Shutdown
    logger.info("TruthLens AI backend shutdown.")


app = FastAPI(
    title="TruthLens AI - Fact Verification & Media Forensics API",
    description="Multi-modal verification engine distinguishing factual veracity, digital media synthesis, and context manipulation.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware configured strictly for development frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global Safe Error Handler to prevent leaking stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred during verification processing. Please try again."}
    )

# Include Routers with API v1 prefix
prefix = settings.API_V1_PREFIX
app.include_router(health_router, prefix=prefix)
app.include_router(auth_router, prefix=prefix)
app.include_router(claims_router, prefix=prefix)
app.include_router(news_router, prefix=prefix)
app.include_router(images_router, prefix=prefix)
app.include_router(videos_router, prefix=prefix)
app.include_router(audio_router, prefix=prefix)
app.include_router(jobs_router, prefix=prefix)
app.include_router(reports_router, prefix=prefix)
app.include_router(history_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount uploads directory for media streaming
if settings.UPLOAD_DIR.exists():
    app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Frontend static asset & SPA serving
frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path == "openapi.json":
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
        target_file = frontend_dist / full_path
        if full_path and target_file.is_file():
            return FileResponse(str(target_file))
        return FileResponse(str(frontend_dist / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs_url": "/docs",
            "api_v1": settings.API_V1_PREFIX,
            "demo_mode": settings.DEMO_MODE
        }
