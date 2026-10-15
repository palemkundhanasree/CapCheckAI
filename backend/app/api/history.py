from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.report_repository import ReportRepository
from app.api.reports import build_report_response
from app.schemas.report import ReportResponse

router = APIRouter(tags=["History"])


@router.get("/history", response_model=List[ReportResponse])
async def get_verification_history(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieves paginated verification report history."""
    report_repo = ReportRepository(db)
    reports = report_repo.list_reports(limit=limit, offset=offset)
    return [build_report_response(r) for r in reports]
