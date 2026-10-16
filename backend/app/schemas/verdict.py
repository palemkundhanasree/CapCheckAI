from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any


class FactualVerdictType(str, Enum):
    SUPPORTED = "SUPPORTED"
    MOSTLY_SUPPORTED = "MOSTLY_SUPPORTED"
    MISLEADING_CONTEXT = "MISLEADING_CONTEXT"
    MOSTLY_CONTRADICTED = "MOSTLY_CONTRADICTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class MediaAuthenticityType(str, Enum):
    AUTHENTIC = "AUTHENTIC"
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    SUSPICIOUS_ARTIFACTS = "SUSPICIOUS_ARTIFACTS"
    AI_GENERATED = "AI_GENERATED"
    MANIPULATED = "MANIPULATED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ContextVerdictType(str, Enum):
    ACCURATE_CONTEXT = "ACCURATE_CONTEXT"
    OUT_OF_CONTEXT = "OUT_OF_CONTEXT"
    MISLEADING_CONTEXT = "MISLEADING_CONTEXT"
    UNVERIFIED = "UNVERIFIED"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class VerdictSynthesis(BaseModel):
    overall_verdict: str
    verdict_label: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    factual_claim_verdict: Optional[str] = None
    media_authenticity_verdict: Optional[str] = None
    context_verdict: Optional[str] = None
    summary: str
    explanation: str
    correctness_score: Optional[float] = None
    correctness_explanation: str = ""
    report_card: Optional[Dict[str, Any]] = None
