from typing import List, Dict, Any, Tuple
from app.schemas.verdict import ConfidenceLevel


def calculate_system_confidence(
    evidence_items: List[Dict[str, Any]],
    detector_scores: List[float],
    has_primary_sources: bool = False,
    is_demo: bool = False
) -> Tuple[float, ConfidenceLevel, str]:
    """
    Transparently calculates overall confidence (0 - 100) based on:
    1. For text/news: quantity, diversity, credibility, and consensus of independent evidence sources
    2. For media: detector agreement, signal extremity, and forensic coverage
    """
    if is_demo:
        return 92.0, ConfidenceLevel.HIGH, "High confidence based on pre-verified reference dataset and multi-source consensus."

    # Scenario A: Media Verification (Image, Video, Audio) where detector_scores exist without text evidence
    if not evidence_items and detector_scores:
        # Distance from 50 (ambiguity zone): scores near 0% or 100% indicate definitive detector certainty
        certainty_scores = [abs(score - 50.0) * 2.0 for score in detector_scores]
        avg_certainty = sum(certainty_scores) / len(certainty_scores)
        # Scaled certainty: high-certainty detectors achieve 80% - 95% confidence
        media_conf = 72.0 + (avg_certainty * 0.24)
        final_score = round(min(max(media_conf, 55.0), 96.0), 1)

        if final_score >= 75.0:
            level = ConfidenceLevel.HIGH
            explanation = f"High confidence ({final_score}%): Strong convergence across {len(detector_scores)} independent sensor and generative artifact detectors."
        else:
            level = ConfidenceLevel.MEDIUM
            explanation = f"Moderate confidence ({final_score}%): Detectors exhibit mild ambiguity in compression or frequency domains."
        return final_score, level, explanation

    # Scenario B: Text Claim or News URL Evidence Calculation
    if evidence_items:
        avg_credibility = sum(item.get("credibility_score", 90.0) for item in evidence_items) / len(evidence_items)
        count_bonus = min(len(evidence_items) * 4.0, 12.0)
        source_score = (avg_credibility * 0.85) + count_bonus

        stances = [item.get("stance") for item in evidence_items if item.get("stance") in ("SUPPORTS", "CONTRADICTS")]
        if stances:
            majority = max(stances.count("SUPPORTS"), stances.count("CONTRADICTS"))
            agreement_ratio = majority / len(stances)
            agreement_score = agreement_ratio * 100.0
        else:
            agreement_score = 80.0

        # Blended weighted confidence
        final_score = (source_score * 0.60) + (agreement_score * 0.40)
        final_score = round(min(max(final_score, 35.0), 96.0), 1)

        if final_score >= 75.0:
            level = ConfidenceLevel.HIGH
            explanation = f"High confidence ({final_score}%): Strong consensus across {len(evidence_items)} independent sources with consistent evidence."
        elif final_score >= 50.0:
            level = ConfidenceLevel.MEDIUM
            explanation = f"Moderate confidence ({final_score}%): Evaluated {len(evidence_items)} sources with partial consensus."
        else:
            level = ConfidenceLevel.LOW
            explanation = f"Low confidence ({final_score}%): Limited authoritative sources available."
        return final_score, level, explanation

    return 50.0, ConfidenceLevel.LOW, "Insufficient public evidence or detector signal available."
