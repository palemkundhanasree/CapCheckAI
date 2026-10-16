import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.report_repository import ReportRepository
from app.api.reports import build_report_response
from app.schemas.report import ReportResponse
from app.security.authentication import require_user, TokenData

logger = logging.getLogger(__name__)
router = APIRouter(tags=["History"])


@router.get("/history", response_model=List[ReportResponse])
async def get_verification_history(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_user)
):
    """Retrieves paginated verification report history.

    A single damaged record is skipped (and logged) instead of failing the whole list.
    """
    report_repo = ReportRepository(db)
    reports = report_repo.list_reports(limit=limit, offset=offset, user_id=user.uid)
    results: List[ReportResponse] = []
    for r in reports:
        try:
            results.append(build_report_response(r))
        except Exception as e:  # noqa: BLE001
            logger.warning("Skipping unreadable report %s in history: %s", getattr(r, "id", "?"), e)
    return results
