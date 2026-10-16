import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Report, EvidenceItem, MediaAnalysis


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        job_id: str,
        title: str,
        input_type: str,
        overall_verdict: str,
        verdict_label: str,
        confidence_score: float,
        confidence_level: str,
        summary: str,
        explanation: str,
        limitations: List[str],
        checks_performed: List[str],
        checks_unavailable: List[str],
        factual_claim_verdict: Optional[str] = None,
        media_authenticity_verdict: Optional[str] = None,
        context_verdict: Optional[str] = None,
        correctness_score: Optional[float] = None,
        correctness_explanation: Optional[str] = None,
        report_card: Optional[Dict[str, Any]] = None,
        input_preview: Optional[str] = None,
        evidence_items: Optional[List[Dict[str, Any]]] = None,
        media_analysis_data: Optional[Dict[str, Any]] = None,
    ) -> Report:
        from app.db.models import VerificationJob
        job = self.db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
        report = Report(
            job_id=job_id,
            user_id=job.user_id if job else None,
            title=title,
            input_type=input_type,
            input_preview=input_preview or title,
            overall_verdict=overall_verdict,
            verdict_label=verdict_label,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            summary=summary,
            explanation=explanation,
            limitations=json.dumps(limitations or []),
            checks_performed=json.dumps(checks_performed or []),
            checks_unavailable=json.dumps(checks_unavailable or []),
            factual_claim_verdict=factual_claim_verdict,
            media_authenticity_verdict=media_authenticity_verdict,
            context_verdict=context_verdict,
            correctness_score=correctness_score,
            correctness_explanation=correctness_explanation,
            report_card=json.dumps(report_card) if report_card else None
        )
        self.db.add(report)
        self.db.flush()

        if evidence_items:
            for item in evidence_items:
                ev = EvidenceItem(
                    report_id=report.id,
                    title=item.get("title", "Untitled Source"),
                    source_name=item.get("source_name", "Web Reference"),
                    source_url=item.get("source_url"),
                    publisher=item.get("publisher"),
                    publish_date=item.get("publish_date"),
                    snippet=item.get("snippet", ""),
                    stance=item.get("stance", "NEUTRAL"),
                    credibility_score=item.get("credibility_score", 70.0)
                )
                self.db.add(ev)

        if media_analysis_data:
            ma = MediaAnalysis(
                report_id=report.id,
                media_type=media_analysis_data.get("media_type", "image"),
                file_path=media_analysis_data.get("file_path"),
                file_size_bytes=media_analysis_data.get("file_size_bytes", 0),
                mime_type=media_analysis_data.get("mime_type"),
                metadata_info=json.dumps(media_analysis_data.get("metadata_info", {})),
                visual_findings=json.dumps(media_analysis_data.get("visual_findings", {})),
                audio_findings=json.dumps(media_analysis_data.get("audio_findings", {})),
                transcript=media_analysis_data.get("transcript"),
                ai_generated_score=media_analysis_data.get("ai_generated_score", 0.0),
                deepfake_score=media_analysis_data.get("deepfake_score", 0.0),
                manipulation_indicators=json.dumps(media_analysis_data.get("manipulation_indicators", []))
            )
            self.db.add(ma)

        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_report_by_job_id(self, job_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.job_id == job_id).first()

    def list_reports(self, limit: int = 50, offset: int = 0, user_id: Optional[str] = None) -> List[Report]:
        q = self.db.query(Report)
        if user_id:
            q = q.filter(Report.user_id == user_id)
        return q.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()

    def delete_report(self, report_id: str) -> bool:
        report = self.get_report_by_id(report_id)
        if not report:
            return False

        # Gather files to delete if media analysis was stored
        files_to_remove = []
        if report.media_analysis and report.media_analysis.file_path:
            files_to_remove.append(report.media_analysis.file_path)

        self.db.delete(report)
        self.db.commit()

        # Safely remove media files
        from app.security.retention import delete_associated_files
        delete_associated_files(files_to_remove)

        return True
