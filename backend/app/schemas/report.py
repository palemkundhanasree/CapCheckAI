from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas.evidence import EvidenceItemSchema


class MediaAnalysisDetail(BaseModel):
    id: str
    media_type: str
    file_path: Optional[str] = None
    file_size_bytes: int
    mime_type: Optional[str] = None
    metadata_info: Dict[str, Any] = {}
    visual_findings: Dict[str, Any] = {}
    audio_findings: Dict[str, Any] = {}
    transcript: Optional[str] = None
    ai_generated_score: float = 0.0
    deepfake_score: float = 0.0
    manipulation_indicators: List[str] = []


class ReportResponse(BaseModel):
    id: str
    job_id: str
    title: str
    input_type: str
    overall_verdict: str
    verdict_label: str
    confidence_score: float
    confidence_level: str
    factual_claim_verdict: Optional[str] = None
    media_authenticity_verdict: Optional[str] = None
    context_verdict: Optional[str] = None
    summary: str
    explanation: str
    correctness_score: Optional[float] = None
    correctness_explanation: Optional[str] = None
    report_card: Optional[Dict[str, Any]] = None
    limitations: List[str] = []
    checks_performed: List[str] = []
    checks_unavailable: List[str] = []
    created_at: datetime
    input_preview: Optional[str] = None
    media_url: Optional[str] = None
    evidence_items: List[EvidenceItemSchema] = []
    media_analysis: Optional[MediaAnalysisDetail] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    id: str
    job_type: str
    status: str  # queued, processing, completed, failed
    progress: int
    current_stage: str
    report_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobStatusResponse]
