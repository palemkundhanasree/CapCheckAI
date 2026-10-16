from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.report_repository import ReportRepository
from app.api.reports import build_report_response
from app.schemas.report import ReportResponse
from app.security.authentication import require_authenticated_user, get_user_id_from_token, TokenData

router = APIRouter(tags=["History"])


@router.get("/history", response_model=List[ReportResponse])
async def get_verification_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    all_users: bool = Query(False),
    token_data: TokenData = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Retrieves isolated, individual verification history for the authenticated user."""
    user_id = get_user_id_from_token(token_data, db)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not recognized. Please sign in again."
        )

    report_repo = ReportRepository(db)
    # Strictly isolate individual data: only admins with explicit all_users=True see global logs
    if all_users and token_data.role == "admin":
        reports = report_repo.list_reports(limit=limit, offset=offset, include_all=True)
    else:
        reports = report_repo.list_reports(limit=limit, offset=offset, user_id=user_id)

    return [build_report_response(r) for r in reports]
