import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.repositories.report_repository import ReportRepository
from app.schemas.report import ReportResponse, MediaAnalysisDetail
from app.services.report_generator import generate_pdf_report
from app.security.authentication import get_current_user_optional, get_user_id_from_token, TokenData

router = APIRouter(tags=["Reports"])


def build_report_response(report) -> ReportResponse:
    # Deserialize JSON fields
    limitations = json.loads(report.limitations) if report.limitations else []
    checks_performed = json.loads(report.checks_performed) if report.checks_performed else []
    checks_unavailable = json.loads(report.checks_unavailable) if report.checks_unavailable else []

    media_detail = None
    if report.media_analysis:
        ma = report.media_analysis
        media_detail = MediaAnalysisDetail(
            id=ma.id,
            media_type=ma.media_type,
            file_path=ma.file_path,
            file_size_bytes=ma.file_size_bytes,
            mime_type=ma.mime_type,
            metadata_info=json.loads(ma.metadata_info) if ma.metadata_info else {},
            visual_findings=json.loads(ma.visual_findings) if ma.visual_findings else {},
            audio_findings=json.loads(ma.audio_findings) if ma.audio_findings else {},
            transcript=ma.transcript,
            ai_generated_score=ma.ai_generated_score,
            deepfake_score=ma.deepfake_score,
            manipulation_indicators=json.loads(ma.manipulation_indicators) if ma.manipulation_indicators else []
        )

    media_url = None
    if report.media_analysis and report.media_analysis.file_path:
        file_p = Path(report.media_analysis.file_path)
        if file_p.exists():
            media_url = f"/api/v1/reports/{report.id}/media"

    return ReportResponse(
        id=report.id,
        job_id=report.job_id,
        title=report.title,
        input_type=report.input_type,
        overall_verdict=report.overall_verdict,
        verdict_label=report.verdict_label,
        confidence_score=report.confidence_score,
        confidence_level=report.confidence_level,
        factual_claim_verdict=report.factual_claim_verdict,
        media_authenticity_verdict=report.media_authenticity_verdict,
        context_verdict=report.context_verdict,
        summary=report.summary,
        explanation=report.explanation,
        limitations=limitations,
        checks_performed=checks_performed,
        checks_unavailable=checks_unavailable,
        created_at=report.created_at,
        input_preview=report.input_preview or report.title,
        media_url=media_url,
        evidence_items=report.evidence_items,
        media_analysis=media_detail
    )


def assert_report_access(report, token_data: Optional[TokenData], db: Session):
    """Enforces that users can only access their own verification dossiers unless admin."""
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    is_admin = token_data and token_data.role == "admin"
    if is_admin:
        return
    current_uid = get_user_id_from_token(token_data, db)
    if not current_uid or report.user_id != current_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This verification record is protected and belongs to another user account."
        )


@router.get("/reports/{report_id}/media")
async def get_report_media_file(
    report_id: str,
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Serves the uploaded input media file (image, video, audio) with data isolation security."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if not report or not report.media_analysis or not report.media_analysis.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found.")

    assert_report_access(report, token_data, db)

    file_p = Path(report.media_analysis.file_path)
    if not file_p.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file has been shredded or expired.")

    mime_type = report.media_analysis.mime_type or "application/octet-stream"
    return FileResponse(path=str(file_p), media_type=mime_type)


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report_endpoint(
    report_id: str,
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieves full verification dossier by Report ID with individual user security."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    assert_report_access(report, token_data, db)

    return build_report_response(report)


@router.delete("/reports/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report_endpoint(
    report_id: str,
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Deletes report and immediately shreds all associated media files with user ownership verification."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    assert_report_access(report, token_data, db)

    deleted = report_repo.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return {"message": "Report and associated uploaded files deleted successfully.", "report_id": report_id}


@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Generates and downloads official PDF report dossier with user security."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    assert_report_access(report, token_data, db)

    response_data = build_report_response(report).dict()
    pdf_path = settings.REPORT_DIR / f"capcheck_report_{report.id}.pdf"

    generated_path = generate_pdf_report(response_data, pdf_path)

    media_type = "application/pdf" if str(generated_path).endswith(".pdf") else "text/plain"
    filename = f"CapCheck_Report_{report.id[:8]}.pdf" if media_type == "application/pdf" else f"CapCheck_Report_{report.id[:8]}.txt"

    return FileResponse(
        path=str(generated_path),
        media_type=media_type,
        filename=filename
    )
