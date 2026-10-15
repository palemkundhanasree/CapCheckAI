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
    1. Quantity and diversity of independent evidence sources
    2. Consensus / agreement ratio among sources
    3. Average credibility score of sources
    4. Detector agreement and coverage
    """
    if is_demo:
        return 92.0, ConfidenceLevel.HIGH, "High confidence based on pre-verified reference dataset and multi-source consensus."

    # Factor 1: Evidence source count and credibility
    source_score = 0.0
    if evidence_items:
        avg_credibility = sum(item.get("credibility_score", 60.0) for item in evidence_items) / len(evidence_items)
        count_bonus = min(len(evidence_items) * 8.0, 30.0)
        source_score = (avg_credibility * 0.7) + count_bonus
    else:
        source_score = 25.0

    # Factor 2: Consensus / stance agreement
    stances = [item.get("stance") for item in evidence_items if item.get("stance") in ("SUPPORTS", "CONTRADICTS")]
    agreement_score = 50.0
    if stances:
        majority = max(stances.count("SUPPORTS"), stances.count("CONTRADICTS"))
        ratio = majority / len(stances)
        agreement_score = ratio * 100.0

    # Factor 3: Detector coverage & extremity
    detector_score = 60.0
    if detector_scores:
        # Distance from 50 (ambiguous zone)
        distances = [abs(score - 50.0) * 2.0 for score in detector_scores]
        detector_score = sum(distances) / len(distances)

    # Composite calculation
    weights = [0.45, 0.35, 0.20]
    final_score = (source_score * weights[0]) + (agreement_score * weights[1]) + (detector_score * weights[2])
    final_score = round(min(max(final_score, 15.0), 96.0), 1)

    if final_score >= 75.0:
        level = ConfidenceLevel.HIGH
        explanation = f"High confidence ({final_score}%): Strong consensus across {len(evidence_items)} independent sources with consistent forensic indicators."
    elif final_score >= 50.0:
        level = ConfidenceLevel.MEDIUM
        explanation = f"Moderate confidence ({final_score}%): Evaluated {len(evidence_items)} sources; partial consensus or limited independent corroboration."
    else:
        level = ConfidenceLevel.LOW
        explanation = f"Low confidence ({final_score}%): Weak or inconclusive signals with limited authoritative sources available."

    return final_score, level, explanation
