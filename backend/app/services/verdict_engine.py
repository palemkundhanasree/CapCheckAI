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
    Synthesizes multi-modal signals into clear, easy-to-understand verdicts:
    1. Factual claim truthfulness (Is the statement true or false?)
    2. Media artifact authenticity (Was it taken by a real camera or made by AI?)
    3. Contextual framing (Is it old media being used with a fake caption?)
    """

    @staticmethod
    def evaluate_claim_verdict(evidence_items: List[Dict[str, Any]]) -> str:
        """Determines factual claim truthfulness based on supporting vs contradicting evidence."""
        if not evidence_items:
            return FactualVerdictType.INCONCLUSIVE.value

        supporting_weight = sum(
            item.get("credibility_score", 50.0) for item in evidence_items if item.get("stance") == "SUPPORTS"
        )
        contradicting_weight = sum(
            item.get("credibility_score", 50.0) for item in evidence_items if item.get("stance") == "CONTRADICTS"
        )
        context_items = [item for item in evidence_items if item.get("stance") == "CONTEXT"]

        if contradicting_weight > supporting_weight * 1.5:
            return FactualVerdictType.CONTRADICTED.value
        elif contradicting_weight > supporting_weight:
            return FactualVerdictType.MOSTLY_CONTRADICTED.value
        elif supporting_weight > contradicting_weight * 1.5:
            return FactualVerdictType.SUPPORTED.value
        elif supporting_weight > contradicting_weight:
            return FactualVerdictType.MOSTLY_SUPPORTED.value
        elif context_items and not (supporting_weight or contradicting_weight):
            return FactualVerdictType.MISLEADING_CONTEXT.value

        return FactualVerdictType.INCONCLUSIVE.value

    @staticmethod
    def evaluate_media_authenticity(
        ai_score: float,
        manipulation_score: float,
        indicators: List[str],
        has_c2pa: bool = False,
        is_c2pa_ai: bool = False
    ) -> str:
        """Determines physical authenticity vs synthetic generation or alteration."""
        if is_c2pa_ai:
            return MediaAuthenticityType.AI_GENERATED.value

        max_risk = max(ai_score, manipulation_score)

        if max_risk >= 60.0:
            return MediaAuthenticityType.AI_GENERATED.value if ai_score >= manipulation_score else MediaAuthenticityType.MANIPULATED.value
        elif max_risk >= 40.0:
            return MediaAuthenticityType.SUSPICIOUS_ARTIFACTS.value
        elif max_risk <= 25.0:
            return MediaAuthenticityType.AUTHENTIC.value
        elif max_risk <= 35.0:
            return MediaAuthenticityType.LIKELY_AUTHENTIC.value

        return MediaAuthenticityType.INCONCLUSIVE.value

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
        """Combines the 3 pillars into a simple, user-friendly final verdict with high clarity."""
        conf_score, conf_level, conf_explanation = calculate_system_confidence(
            evidence_items=evidence_items,
            detector_scores=detector_scores
        )

        overall_verdict = "INCONCLUSIVE"
        verdict_label = "Unverified / Needs More Evidence"
        summary = ""

        # 1. Text Claim or News URL input
        if input_type in ("claim", "url"):
            overall_verdict = factual_verdict or "INCONCLUSIVE"
            if overall_verdict == FactualVerdictType.SUPPORTED.value:
                verdict_label = "Supported / True (Confirmed by Facts)"
                summary = "This statement is true and verified by independent news reporting, scientific consensus, or official records."
            elif overall_verdict == FactualVerdictType.MOSTLY_SUPPORTED.value:
                verdict_label = "Mostly Supported / Likely True"
                summary = "The main claim is true and supported by credible records, with minor details or variations noted."
            elif overall_verdict == FactualVerdictType.MISLEADING_CONTEXT.value:
                verdict_label = "Misleading (Missing Important Context)"
                summary = "This claim contains some real elements, but is presented in a misleading way or leaves out crucial context."
            elif overall_verdict == FactualVerdictType.MOSTLY_CONTRADICTED.value:
                verdict_label = "Mostly Contradicted / Likely False"
                summary = "Public evidence and verified records contradict the main point of this statement."
            elif overall_verdict == FactualVerdictType.CONTRADICTED.value:
                verdict_label = "Contradicted / False (Debunked Hoax)"
                summary = "This claim has been proven false and contradicted by credible independent sources or official documentation."
            else:
                verdict_label = "Unverified (Insufficient Evidence)"
                summary = "We could not find enough verified public records to definitively prove or disprove this claim."

        # 2. Media Inputs (Image, Video, Audio)
        else:
            if media_verdict in (MediaAuthenticityType.AI_GENERATED.value, MediaAuthenticityType.MANIPULATED.value):
                overall_verdict = media_verdict
                if media_verdict == MediaAuthenticityType.AI_GENERATED.value:
                    verdict_label = "AI-Generated (Fake Media)"
                    summary = "This media was generated by artificial intelligence (like Midjourney, DALL-E, or AI voice cloning)."
                else:
                    verdict_label = "Digitally Altered (Photoshopped)"
                    summary = "This media was edited or spliced. Noticeable compression mismatches or tampering were detected."
            elif media_verdict == MediaAuthenticityType.SUSPICIOUS_ARTIFACTS.value:
                overall_verdict = "SUSPICIOUS"
                verdict_label = "Suspicious Edits Detected"
                summary = "This file shows borderline editing signals or heavy filters that may conceal alterations."
            elif media_verdict in (MediaAuthenticityType.AUTHENTIC.value, MediaAuthenticityType.LIKELY_AUTHENTIC.value):
                if context_verdict == ContextVerdictType.MISLEADING_CONTEXT.value:
                    overall_verdict = "MISLEADING_CONTEXT"
                    verdict_label = "Real Media, Fake Story (Wrong Context)"
                    summary = "The image or video is a genuine camera capture, but it is being recycled or described with a false caption/date."
                else:
                    overall_verdict = "AUTHENTIC"
                    verdict_label = "Real Camera Media (Authentic)"
                    summary = "This media is genuine. Forensic tests show natural camera sensor noise, correct frequencies, and zero AI generation."
            else:
                overall_verdict = "INCONCLUSIVE"
                verdict_label = "Inconclusive / Low Quality"
                summary = "The file resolution or quality is too low to definitively confirm authenticity or manipulation."

        # Build comprehensive readable explanation in plain English
        explanation_parts = [
            f"**Quick Summary**: {summary}",
            f"\n\n**Confidence Level**: {conf_score}% certainty ({conf_explanation})",
            "\n\n**Three-Point Check Breakdown**:"
        ]
        if factual_verdict:
            simple_fact = factual_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **1. Fact Check**: {simple_fact} — Based on {len(evidence_items)} referenced fact-check and encyclopedia sources.")
        if media_verdict:
            simple_media = media_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **2. Media Authenticity**: {simple_media} — Analyzed using camera metadata, noise distribution, and frequency scans.")
        if context_verdict:
            simple_context = context_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **3. Context & Caption**: {simple_context} — Verified against recording timestamps and event history.")

        if indicators:
            explanation_parts.append(f"\n\n**Key Clues Found**: {'; '.join(indicators)}.")

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
