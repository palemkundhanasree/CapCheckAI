import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.repositories.report_repository import ReportRepository
from app.schemas.report import ReportResponse, MediaAnalysisDetail
from app.services.report_generator import generate_pdf_report
from app.security.authentication import require_user, can_access, TokenData

router = APIRouter(tags=["Reports"])


def _safe_json(raw, default):
    """json.loads that never raises: bad/empty data gives the default instead of a 500 error."""
    if not raw:
        return default
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return default
    return value if isinstance(value, type(default)) else default


def build_report_response(report) -> ReportResponse:
    # Deserialize JSON fields (tolerant: one damaged old record must never break the page)
    limitations = _safe_json(report.limitations, [])
    checks_performed = _safe_json(report.checks_performed, [])
    checks_unavailable = _safe_json(report.checks_unavailable, [])

    try:
        report_card = json.loads(report.report_card) if report.report_card else None
    except (ValueError, TypeError):
        report_card = None

    media_detail = None
    if report.media_analysis:
        ma = report.media_analysis
        media_detail = MediaAnalysisDetail(
            id=ma.id,
            media_type=ma.media_type,
            file_path=ma.file_path,
            file_size_bytes=ma.file_size_bytes or 0,
            mime_type=ma.mime_type,
            metadata_info=_safe_json(ma.metadata_info, {}),
            visual_findings=_safe_json(ma.visual_findings, {}),
            audio_findings=_safe_json(ma.audio_findings, {}),
            transcript=ma.transcript,
            ai_generated_score=ma.ai_generated_score or 0.0,
            deepfake_score=ma.deepfake_score or 0.0,
            manipulation_indicators=_safe_json(ma.manipulation_indicators, [])
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
        confidence_score=report.confidence_score or 0.0,
        confidence_level=report.confidence_level or "LOW",
        factual_claim_verdict=report.factual_claim_verdict,
        media_authenticity_verdict=report.media_authenticity_verdict,
        context_verdict=report.context_verdict,
        summary=report.summary or "",
        explanation=report.explanation or "",
        correctness_score=report.correctness_score,
        correctness_explanation=report.correctness_explanation,
        report_card=report_card,
        limitations=limitations,
        checks_performed=checks_performed,
        checks_unavailable=checks_unavailable,
        created_at=report.created_at or datetime.utcnow(),
        input_preview=report.input_preview or report.title,
        media_url=media_url,
        evidence_items=report.evidence_items,
        media_analysis=media_detail
    )


@router.get("/reports/{report_id}/media")
async def get_report_media_file(report_id: str, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Serves the uploaded input media file (image, video, audio) for preview in the UI."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if report and not can_access(report.user_id, user):
        report = None
    if not report or not report.media_analysis or not report.media_analysis.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found.")

    file_p = Path(report.media_analysis.file_path)
    if not file_p.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file has been shredded or expired.")

    mime_type = report.media_analysis.mime_type or "application/octet-stream"
    return FileResponse(path=str(file_p), media_type=mime_type)



@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report_endpoint(report_id: str, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Retrieves full verification dossier by Report ID."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if report and not can_access(report.user_id, user):
        report = None
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return build_report_response(report)


@router.delete("/reports/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report_endpoint(report_id: str, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Deletes report and immediately shreds all associated media files."""
    report_repo = ReportRepository(db)
    deleted = report_repo.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return {"message": "Report and associated uploaded files deleted successfully.", "report_id": report_id}


@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(report_id: str, db: Session = Depends(get_db), user: TokenData = Depends(require_user)):
    """Generates and downloads official PDF report dossier."""
    report_repo = ReportRepository(db)
    report = report_repo.get_report_by_id(report_id)
    if report and not can_access(report.user_id, user):
        report = None
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    response_data = build_report_response(report).dict()
    pdf_path = settings.REPORT_DIR / f"truthlens_report_{report.id}.pdf"

    generated_path = generate_pdf_report(response_data, pdf_path)

    media_type = "application/pdf" if str(generated_path).endswith(".pdf") else "text/plain"
    filename = f"CapCheck_Report_{report.id[:8]}.pdf" if media_type == "application/pdf" else f"CapCheck_Report_{report.id[:8]}.txt"

    return FileResponse(
        path=str(generated_path),
        media_type=media_type,
        filename=filename
    )
