from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, VerificationJob, Report
from app.schemas.request import AdminLoginRequest
from app.security.authentication import verify_password, create_access_token, require_admin_user, TokenData
from app.security.retention import cleanup_expired_files

router = APIRouter(tags=["Administration"])


@router.post("/admin/login")
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin login endpoint issuing JWT bearer token."""
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password."
        )

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }


@router.get("/admin/stats")
async def get_system_stats(
    token: TokenData = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """Admin dashboard stats and system volume metrics."""
    total_jobs = db.query(VerificationJob).count()
    completed_jobs = db.query(VerificationJob).filter(VerificationJob.status == "completed").count()
    failed_jobs = db.query(VerificationJob).filter(VerificationJob.status == "failed").count()
    total_reports = db.query(Report).count()

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "total_reports": total_reports,
        "status": "operational"
    }


@router.post("/admin/purge-old-files")
async def purge_old_uploads(
    token: TokenData = Depends(require_admin_user)
):
    """Manually triggers retention policy file cleanup."""
    purged = cleanup_expired_files(max_age_hours=24)
    return {"message": f"Successfully purged {purged} temporary files older than 24h."}
