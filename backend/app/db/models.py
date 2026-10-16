import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class VerificationJob(Base):
    __tablename__ = "verification_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    job_type = Column(String(20), nullable=False, index=True)  # claim, url, image, video, audio
    status = Column(String(20), nullable=False, default="queued", index=True)  # queued, processing, completed, failed
    progress = Column(Integer, default=0)
    current_stage = Column(String(100), default="Initializing analysis")
    input_data = Column(Text, nullable=True)  # JSON representation of input parameters or paths
    error_message = Column(Text, nullable=True)
    report_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="job", uselist=False, cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    job_id = Column(String(36), ForeignKey("verification_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    input_type = Column(String(20), nullable=False)
    input_preview = Column(Text, nullable=True)
    
    # 3 Separate Distinct Verification Pillars
    factual_claim_verdict = Column(String(50), nullable=True)     # SUPPORTED, CONTRADICTED, etc.
    media_authenticity_verdict = Column(String(50), nullable=True) # AUTHENTIC, AI_GENERATED, MANIPULATED, etc.
    context_verdict = Column(String(50), nullable=True)           # ACCURATE_CONTEXT, MISLEADING_CONTEXT, etc.

    # Overall Synthesis
    overall_verdict = Column(String(50), nullable=False)
    verdict_label = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 100.0
    confidence_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH

    summary = Column(Text, nullable=False)
    correctness_score = Column(Float, nullable=True)  # 0-100 likelihood the input is correct/genuine
    correctness_explanation = Column(Text, nullable=True)
    report_card = Column(Text, nullable=True)  # JSON: per-test breakdown shown as the report card
    explanation = Column(Text, nullable=False)
    limitations = Column(Text, default="[]")  # JSON encoded list of known limitations
    checks_performed = Column(Text, default="[]")  # JSON encoded list
    checks_unavailable = Column(Text, default="[]")  # JSON encoded list
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    job = relationship("VerificationJob", back_populates="report")
    evidence_items = relationship("EvidenceItem", back_populates="report", cascade="all, delete-orphan")
    media_analysis = relationship("MediaAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source_name = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=True)
    publisher = Column(String(100), nullable=True)
    publish_date = Column(String(50), nullable=True)
    snippet = Column(Text, nullable=False)
    stance = Column(String(30), nullable=False)  # SUPPORTS, CONTRADICTS, NEUTRAL, CONTEXT
    credibility_score = Column(Float, default=70.0)

    report = relationship("Report", back_populates="evidence_items")


class MediaAnalysis(Base):
    __tablename__ = "media_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type = Column(String(20), nullable=False)  # image, video, audio
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)

    metadata_info = Column(Text, default="{}")  # JSON encoded EXIF / container tags
    visual_findings = Column(Text, default="{}")  # JSON encoded frame/image findings
    audio_findings = Column(Text, default="{}")  # JSON encoded speech & waveform analysis
    transcript = Column(Text, nullable=True)     # Extracted speech-to-text transcript

    ai_generated_score = Column(Float, default=0.0)   # 0 to 100
    deepfake_score = Column(Float, default=0.0)       # 0 to 100
    manipulation_indicators = Column(Text, default="[]")  # JSON encoded list

    report = relationship("Report", back_populates="media_analysis")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=True, index=True)
    name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # admin, user
    otp_code = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
