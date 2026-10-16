from typing import List, Dict, Any, Tuple
from app.schemas.verdict import ConfidenceLevel


def calculate_system_confidence(
    evidence_items: List[Dict[str, Any]],
    detector_scores: List[float],
    has_primary_sources: bool = False,
    is_demo: bool = False
) -> Tuple[float, ConfidenceLevel, str]:
    """
    Confidence (0-100) in the verdict that is shown. It is built only from what was actually found:
      - evidence: independent sources that clearly SUPPORT or CONTRADICT the claim, weighted by source reliability
      - agreement: how many of those sources point the same way
      - forensics: how far each media detector score is from the uncertain middle (50)
    Background references and unrelated hits are ignored. No evidence means low confidence.
    """
    decisive = [e for e in evidence_items if e.get("stance") in ("SUPPORTS", "CONTRADICTS")]
    parts: List[str] = []
    components: List[Tuple[float, float]] = []  # (score, weight)

    if evidence_items or not detector_scores:
        if decisive:
            publishers = {(e.get("publisher") or e.get("source_name") or "").lower() for e in decisive}
            avg_rel = sum(e.get("credibility_score", 60.0) for e in decisive) / len(decisive)
            independence = min(len(publishers), 4) / 4 * 30.0
            evidence_score = min(avg_rel * 0.7 + independence, 100.0)
            sup = sum(1 for e in decisive if e["stance"] == "SUPPORTS")
            con = len(decisive) - sup
            agreement = max(sup, con) / len(decisive) * 100.0
            components += [(evidence_score, 0.55), (agreement, 0.45)]
            parts.append(f"{len(decisive)} source(s) took a clear position ({sup} supporting, {con} contradicting) from {len(publishers)} independent publisher(s), average reliability {avg_rel:.0f}/100")
        else:
            parts.append("no source took a clear position on this claim")
            components.append((15.0, 1.0))

    if detector_scores:
        strength = sum(abs(s - 50.0) * 2.0 for s in detector_scores) / len(detector_scores)
        components.append((strength, 0.5 if components else 1.0))
        parts.append(f"{len(detector_scores)} forensic detector(s) averaged {sum(detector_scores)/len(detector_scores):.0f}/100 risk, which is {'clearly away from' if strength >= 50 else 'close to'} the uncertain middle")

    total_w = sum(w for _, w in components) or 1.0
    score = sum(s * w for s, w in components) / total_w
    if not decisive and evidence_items is not None and not detector_scores:
        score = min(score, 30.0)
    final_score = round(min(max(score, 10.0), 95.0), 1)

    if final_score >= 75.0:
        level = ConfidenceLevel.HIGH
    elif final_score >= 50.0:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
    explanation = f"{level.value.title()} confidence ({final_score}%): " + "; ".join(parts) + "."
    return final_score, level, explanation
