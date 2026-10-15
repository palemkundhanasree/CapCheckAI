from typing import List, Dict, Any, Optional
from app.schemas.verdict import (
    FactualVerdictType,
    MediaAuthenticityType,
    ContextVerdictType,
    ConfidenceLevel,
    VerdictSynthesis
)
from app.services.confidence_service import calculate_system_confidence


class VerdictEngine:
    """
    CapCheck AI Verification Engine.
    Strict Rule: Information and media must achieve at least 75% verified support
    from credible internet sources and forensic detectors to be classified as Real (Green).
    Otherwise, the item is classified as Fake / False (Red).
    """

    MIN_REAL_THRESHOLD: float = 75.0  # Strict 75% threshold

    @staticmethod
    def evaluate_claim_verdict(evidence_items: List[Dict[str, Any]]) -> str:
        """
        Determines factual claim truthfulness based on supporting vs contradicting evidence.
        Requires at least 75% supporting weight from internet sources to be SUPPORTED.
        Otherwise classified as CONTRADICTED.
        """
        if not evidence_items:
            return FactualVerdictType.CONTRADICTED.value

        supporting_weight = sum(
            item.get("credibility_score", 50.0) for item in evidence_items if item.get("stance") == "SUPPORTS"
        )
        contradicting_weight = sum(
            item.get("credibility_score", 50.0) for item in evidence_items if item.get("stance") == "CONTRADICTS"
        )
        total_weight = supporting_weight + contradicting_weight

        support_ratio = (supporting_weight / total_weight * 100.0) if total_weight > 0 else 0.0

        # At least 75% supporting ratio required, and minimal contradictions
        if support_ratio >= VerdictEngine.MIN_REAL_THRESHOLD and contradicting_weight <= supporting_weight * 0.25:
            return FactualVerdictType.SUPPORTED.value
        else:
            return FactualVerdictType.CONTRADICTED.value

    @staticmethod
    def evaluate_media_authenticity(
        ai_score: float,
        manipulation_score: float,
        indicators: List[str],
        has_c2pa: bool = False,
        is_c2pa_ai: bool = False
    ) -> str:
        """
        Determines physical authenticity vs synthetic generation or alteration.
        Requires at least 75% physical authenticity (AI risk <= 25% and manipulation <= 25%).
        """
        if is_c2pa_ai:
            return MediaAuthenticityType.AI_GENERATED.value

        max_risk = max(ai_score, manipulation_score)
        authenticity_score = 100.0 - max_risk

        if authenticity_score >= VerdictEngine.MIN_REAL_THRESHOLD:
            return MediaAuthenticityType.AUTHENTIC.value
        else:
            if ai_score >= manipulation_score:
                return MediaAuthenticityType.AI_GENERATED.value
            else:
                return MediaAuthenticityType.MANIPULATED.value

    @staticmethod
    def synthesize_overall_verdict(
        input_type: str,
        factual_verdict: Optional[str],
        media_verdict: Optional[str],
        context_verdict: Optional[str],
        evidence_items: List[Dict[str, Any]],
        detector_scores: List[float],
        indicators: List[str],
        summary_hint: str = ""
    ) -> VerdictSynthesis:
        """
        Synthesizes multi-modal signals under CapCheck AI's 75% verification rule:
        - At least 75% verified internet support -> Real / Verified (Green)
        - Below 75% -> Fake / False (Red)
        """
        conf_score, conf_level, conf_explanation = calculate_system_confidence(
            evidence_items=evidence_items,
            detector_scores=detector_scores
        )

        overall_verdict = "CONTRADICTED"
        verdict_label = "Fake / False (Fails 75% Threshold)"
        summary = ""

        # 1. Text Claim or News URL input
        if input_type in ("claim", "url"):
            supporting_items = [e for e in evidence_items if e.get("stance") == "SUPPORTS"]
            contradicting_items = [e for e in evidence_items if e.get("stance") == "CONTRADICTS"]

            supporting_weight = sum(item.get("credibility_score", 50.0) for item in supporting_items)
            contradicting_weight = sum(item.get("credibility_score", 50.0) for item in contradicting_items)
            total_weight = supporting_weight + contradicting_weight
            support_pct = (supporting_weight / total_weight * 100.0) if total_weight > 0 else 0.0

            # Must satisfy both factual verdict AND confidence >= 75%
            is_real = (
                factual_verdict == FactualVerdictType.SUPPORTED.value and
                conf_score >= VerdictEngine.MIN_REAL_THRESHOLD and
                support_pct >= VerdictEngine.MIN_REAL_THRESHOLD
            )

            if is_real:
                overall_verdict = FactualVerdictType.SUPPORTED.value
                verdict_label = f"Real / Verified (Score: {conf_score:.1f}% >= 75%)"
                summary = (
                    f"This news/claim is verified as Real. Reliable internet sources and authoritative factual records "
                    f"confirm the information with a {conf_score:.1f}% confidence score, surpassing CapCheck AI's 75% threshold."
                )
            else:
                overall_verdict = FactualVerdictType.CONTRADICTED.value
                verdict_label = f"Fake / False (Score: {conf_score:.1f}% < 75%)"
                summary = (
                    f"This information does not meet the required 75% internet source verification threshold (Calculated Score: {conf_score:.1f}%). "
                    f"Under CapCheck AI standards, claims lacking at least 75% verified support are classified as Fake / False."
                )

        # 2. Media Inputs (Image, Video, Audio)
        else:
            authenticity_score = 100.0 - max(detector_scores) if detector_scores else 50.0
            is_real_media = (
                media_verdict == MediaAuthenticityType.AUTHENTIC.value and
                authenticity_score >= VerdictEngine.MIN_REAL_THRESHOLD and
                conf_score >= VerdictEngine.MIN_REAL_THRESHOLD
            )

            if is_real_media:
                overall_verdict = "AUTHENTIC"
                verdict_label = f"Real / Verified Media (Authenticity: {authenticity_score:.1f}% >= 75%)"
                summary = (
                    f"This media artifact is verified as genuine camera capture (Authenticity: {authenticity_score:.1f}%). "
                    f"Natural optical sensor noise and frequency spectra are consistent with real-world recording."
                )
            else:
                overall_verdict = "AI_GENERATED" if (detector_scores and detector_scores[0] > 35) else "MANIPULATED"
                verdict_label = f"Fake / Altered Media (Fails 75% Authenticity Threshold)"
                summary = (
                    f"This media fails the 75% authenticity threshold (Score: {authenticity_score:.1f}%). "
                    f"Artificial synthesis, frequency grid anomalies, or digital tampering were detected."
                )

        # Detailed Transparent Explanation
        explanation_parts = [
            f"**CapCheck AI Verification Rule**: Information and media require at least **75.0% verified evidence** across authoritative internet sources and forensic detectors to be classified as Real. Otherwise, the system classifies it as Fake.\n\n",
            f"**Final Verdict**: {verdict_label}\n",
            f"**Calculated Confidence Score**: {conf_score:.1f}% ({conf_explanation})\n\n",
            f"**Verification Summary**: {summary}\n\n",
            f"**Evidence & Multi-Source Audit**:\n"
        ]

        if input_type in ("claim", "url"):
            explanation_parts.append(f"- **Internet Sources Analyzed**: {len(evidence_items)} referenced citations (encyclopedias, fact-checking registries, and web reporting).\n")
            if evidence_items:
                top_sources = [f"*{e.get('source_name', 'Source')}* ({e.get('stance', 'NEUTRAL')})" for e in evidence_items[:4]]
                explanation_parts.append(f"- **Top References**: {', '.join(top_sources)}.\n")
        else:
            if detector_scores:
                ai_val = detector_scores[0] if len(detector_scores) > 0 else 0
                manip_val = detector_scores[1] if len(detector_scores) > 1 else 0
                explanation_parts.append(f"- **AI Generation Risk**: {ai_val:.1f}%\n")
                explanation_parts.append(f"- **Tampering / Manipulation Risk**: {manip_val:.1f}%\n")

        if indicators:
            explanation_parts.append(f"\n**Forensic Clues**: {'; '.join(indicators)}.")

        explanation = "".join(explanation_parts)

        return VerdictSynthesis(
            overall_verdict=overall_verdict,
            verdict_label=verdict_label,
            confidence_score=conf_score,
            confidence_level=conf_level,
            factual_claim_verdict=factual_verdict,
            media_authenticity_verdict=media_verdict,
            context_verdict=context_verdict,
            summary=summary,
            explanation=explanation
        )
