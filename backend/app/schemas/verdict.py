from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CanonicalVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    MIXED = "MIXED"
    UNVERIFIED = "UNVERIFIED"
    ERROR = "ERROR"

    @classmethod
    def normalize(cls, raw: Optional[str], raw_label: Optional[str] = None) -> "CanonicalVerdict":
        clean = str(raw or "").strip().upper()
        if clean in ("SUPPORTED", "AUTHENTIC", "REAL", "VERIFIED", "TRUE", "MOSTLY_SUPPORTED"):
            return cls.SUPPORTED
        if clean in ("FALSE", "FAKE", "CONTRADICTED", "MOSTLY_CONTRADICTED", "AI_GENERATED", "MANIPULATED"):
            return cls.FALSE
        if clean in ("MISLEADING", "MISLEADING_CONTEXT", "OUT_OF_CONTEXT"):
            return cls.MISLEADING
        if clean in ("MIXED", "PARTIALLY_SUPPORTED", "HALF_TRUE"):
            return cls.MIXED
        if clean in ("ERROR", "FAILED"):
            return cls.ERROR
        if clean in ("UNVERIFIED", "INCONCLUSIVE", "OPINION", "UNKNOWN"):
            return cls.UNVERIFIED

        # Check accuracy percentage strings in either raw or raw_label
        combined = (clean + " " + str(raw_label or "").upper()).strip()
        if "0.0%" in combined or "0%" in combined or "FALSE" in combined or "FAKE" in combined or "CONTRADICTED" in combined or "AI-GENERATED" in combined:
            return cls.FALSE
        if "100.0%" in combined or "100%" in combined or "SUPPORTED BY EVIDENCE" in combined:
            return cls.SUPPORTED
        if "MISLEADING" in combined:
            return cls.MISLEADING
        if "MIXED" in combined:
            return cls.MIXED

        return cls.UNVERIFIED


# Legacy compatible aliases
class FactualVerdictType(str, Enum):
    SUPPORTED = "SUPPORTED"
    MOSTLY_SUPPORTED = "SUPPORTED"
    MISLEADING_CONTEXT = "MISLEADING"
    MOSTLY_CONTRADICTED = "FALSE"
    CONTRADICTED = "FALSE"
    INCONCLUSIVE = "UNVERIFIED"
    MIXED = "MIXED"
    UNVERIFIED = "UNVERIFIED"


class MediaAuthenticityType(str, Enum):
    AUTHENTIC = "AUTHENTIC"
    LIKELY_AUTHENTIC = "AUTHENTIC"
    SUSPICIOUS_ARTIFACTS = "MISLEADING"
    AI_GENERATED = "FALSE"
    MANIPULATED = "FALSE"
    INCONCLUSIVE = "UNVERIFIED"


class ContextVerdictType(str, Enum):
    ACCURATE_CONTEXT = "SUPPORTED"
    OUT_OF_CONTEXT = "MISLEADING"
    MISLEADING_CONTEXT = "MISLEADING"
    UNVERIFIED = "UNVERIFIED"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ClaimLevelItem(BaseModel):
    text: str
    verdict: CanonicalVerdict = CanonicalVerdict.UNVERIFIED
    explanation: str = ""


class EvidenceVerificationItem(BaseModel):
    title: str = ""
    url: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    supports_claim: bool = False
    relevance: str = ""


class VerdictSynthesis(BaseModel):
    overall_verdict: str  # Canonical: SUPPORTED | FALSE | MISLEADING | MIXED | UNVERIFIED | ERROR
    verdict_label: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    factual_claim_verdict: Optional[str] = None
    media_authenticity_verdict: Optional[str] = None
    context_verdict: Optional[str] = None
    summary: str
    explanation: str
    claims: List[ClaimLevelItem] = Field(default_factory=list)
    evidence: List[EvidenceVerificationItem] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
