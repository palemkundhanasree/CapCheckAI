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

        decisive = [i for i in evidence_items if i.get("stance") in ("SUPPORTS", "CONTRADICTS")]
        if not decisive:
            context_items = [i for i in evidence_items if i.get("stance") == "CONTEXT"]
            return (FactualVerdictType.MISLEADING_CONTEXT.value if context_items
                    else FactualVerdictType.INCONCLUSIVE.value)

        def weight(stance: str) -> float:
            return sum(i.get("credibility_score", 50.0) for i in decisive if i["stance"] == stance)

        def is_strong(stance: str) -> bool:
            side = [i for i in decisive if i["stance"] == stance]
            publishers = {(i.get("publisher") or i.get("source_name") or "").lower() for i in side}
            return any(i.get("credibility_score", 0) >= 88 and i.get("kind") in ("factcheck", "knowledge") for i in side) or len(publishers) >= 2

        sup, con = weight("SUPPORTS"), weight("CONTRADICTS")
        if con and sup and abs(con - sup) <= 0.25 * max(con, sup):
            return FactualVerdictType.MISLEADING_CONTEXT.value  # credible sources disagree
        if con > sup:
            if not is_strong("CONTRADICTS"):
                return FactualVerdictType.MOSTLY_CONTRADICTED.value
            return FactualVerdictType.CONTRADICTED.value if con > sup * 1.5 else FactualVerdictType.MOSTLY_CONTRADICTED.value
        if not is_strong("SUPPORTS"):
            return FactualVerdictType.MOSTLY_SUPPORTED.value if max(i.get("credibility_score", 0) for i in decisive) >= 70 else FactualVerdictType.INCONCLUSIVE.value
        return FactualVerdictType.SUPPORTED.value if sup > con * 1.5 else FactualVerdictType.MOSTLY_SUPPORTED.value

    @staticmethod
    def evaluate_media_authenticity(
        ai_score: float,
        manipulation_score: float,
        indicators: List[str],
        has_c2pa: bool = False,
        is_c2pa_ai: bool = False,
        has_provenance: bool = False
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
            # Without camera data or Content Credentials, "no warning signs" is not proof of authenticity
            return (MediaAuthenticityType.AUTHENTIC.value if (has_provenance or has_c2pa)
                    else MediaAuthenticityType.LIKELY_AUTHENTIC.value)
        elif max_risk <= 35.0:
            return MediaAuthenticityType.LIKELY_AUTHENTIC.value

        return MediaAuthenticityType.INCONCLUSIVE.value

    @staticmethod
    def estimate_correctness(
        input_type: str,
        evidence_items: List[Dict[str, Any]],
        detector_scores: List[float],
        media_verdict: Optional[str],
        confidence: float,
    ):
        """
        Overall "how likely is this correct / genuine" percentage, with the reasoning behind it.
          - Claims: share of reliable evidence that supports the claim, pulled toward 50% when the
            evidence is thin (one weak source cannot produce 95%).
          - Media: 100 minus the strongest forensic risk score, capped at 88% because automated tests
            can reveal warning signs but can never prove a file is genuine.
          - Both: the lower of the two, since both must hold.
        If nothing reliable took a position the percentage is withheld rather than guessed.
        """
        values: List[float] = []
        notes: List[str] = []

        decisive = [i for i in evidence_items if i.get("stance") in ("SUPPORTS", "CONTRADICTS")]
        if decisive:
            sup = sum(i.get("credibility_score", 50.0) for i in decisive if i["stance"] == "SUPPORTS")
            con = sum(i.get("credibility_score", 50.0) for i in decisive if i["stance"] == "CONTRADICTS")
            share = sup / (sup + con) * 100.0
            publishers = {(i.get("publisher") or i.get("source_name") or "").lower() for i in decisive}
            has_authority = any(i.get("kind") in ("factcheck", "knowledge") and i.get("credibility_score", 0) >= 85 for i in decisive)
            strength = 1.0 if has_authority else (0.8 if len(publishers) >= 2 else 0.55)
            pct = 50.0 + (share - 50.0) * strength
            values.append(min(max(pct, 3.0), 97.0))
            n_sup = sum(1 for i in decisive if i["stance"] == "SUPPORTS")
            notes.append(
                f"Claim: {n_sup} of {len(decisive)} decisive source(s) support it, which is {share:.0f}% of the reliability-weighted evidence. "
                + ("A fact-check or reference record was available, so the evidence is used at full strength."
                   if has_authority else
                   "There was no fact-check or reference record, so the result is pulled toward 50% to reflect the thinner evidence.")
            )

        if detector_scores and input_type in ("image", "video", "audio"):
            risk = max(detector_scores)
            genuine = min(max(100.0 - risk, 2.0), 88.0)
            values.append(genuine)
            notes.append(
                f"Media: the strongest forensic warning score was {risk:.0f}/100, so the file is estimated {genuine:.0f}% likely to be genuine. "
                "This is capped at 88% because automated tests can find signs of AI generation or editing but cannot prove a file is untouched."
            )

        if not values:
            return None, ("A percentage is not given because no reliable source clearly confirmed or denied this, "
                          "and any number would be a guess. Try a more specific claim or add a link to the original report.")
        final = round(min(values), 0)
        if len(values) > 1:
            notes.append(f"Overall: the lower of the two ({final:.0f}%), because the claim and the media must both be right.")
        return final, " ".join(notes)

    # ------------------------------------------------------------------ report card
    GRADE_BANDS = [
        (85.0, "A", "Very likely correct / genuine"),
        (70.0, "B", "Likely correct / genuine"),
        (55.0, "C", "Uncertain, leaning correct"),
        (40.0, "D", "Uncertain, leaning incorrect"),
        (0.0, "F", "Likely false / fake"),
    ]
    EVIDENCE_GROUPS = [
        ("factcheck", "Fact-checker records", "Published fact-checks (for example Snopes, PolitiFact, Google Fact Check)."),
        ("knowledge", "Reference knowledge", "Direct comparison of the statement with reference facts."),
        ("news", "Live news coverage", "Articles found and read from news outlets."),
    ]

    @staticmethod
    def _grade(pct: Optional[float]):
        if pct is None:
            return "?", "Not enough reliable evidence to give a percentage"
        for floor, letter, label in VerdictEngine.GRADE_BANDS:
            if pct >= floor:
                return letter, label
        return "F", "Likely false / fake"

    @staticmethod
    def _status(pct: Optional[float]) -> str:
        if pct is None:
            return "unknown"
        return "good" if pct >= 70 else ("warn" if pct >= 40 else "bad")

    @staticmethod
    def build_report_card(
        input_type: str,
        evidence_items: List[Dict[str, Any]],
        detector_details: Optional[List[Dict[str, Any]]],
        correctness_score: Optional[float],
        correctness_explanation: str,
        confidence_score: float,
        confidence_level: str,
        ai_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Breaks the overall percentage down test by test, so a reader can see WHICH checks pushed it up or down.
        Each section is a 0-100 "how correct/genuine does this test say it is" figure, or None when the test
        could not give a position (shown as "no result", never as a made-up number).
        """
        sections: List[Dict[str, Any]] = []

        # Gemini AI evaluation table (text claims): one row per criterion, all as percentages
        if ai_analysis:
            tp = ai_analysis.get("truth_percent")
            sections.append({
                "key": "gemini", "title": "Gemini AI verdict: chance the statement is true",
                "percent": tp, "status": VerdictEngine._status(tp),
                "detail": ai_analysis.get("summary") or ai_analysis.get("explanation") or "",
            })
            for n, row in enumerate(ai_analysis.get("evaluation", [])):
                sections.append({
                    "key": f"gemini_{n}", "title": f"Gemini: {row['criterion']}",
                    "percent": float(row["percent"]), "status": VerdictEngine._status(float(row["percent"])),
                    "detail": row.get("comment", ""),
                })

        # Evidence-based sections (claims, URLs, captions, spoken claims)
        for kind, title, what in VerdictEngine.EVIDENCE_GROUPS:
            group = [i for i in evidence_items if i.get("kind") == kind]
            if not group and not evidence_items:
                continue
            decisive = [i for i in group if i.get("stance") in ("SUPPORTS", "CONTRADICTS")]
            if decisive:
                sup = sum(i.get("credibility_score", 50.0) for i in decisive if i["stance"] == "SUPPORTS")
                con = sum(i.get("credibility_score", 50.0) for i in decisive if i["stance"] == "CONTRADICTS")
                pct = round(sup / (sup + con) * 100.0, 0)
                n_sup = sum(1 for i in decisive if i["stance"] == "SUPPORTS")
                sections.append({
                    "key": kind, "title": title, "percent": pct, "status": VerdictEngine._status(pct),
                    "detail": f"{what} {n_sup} of {len(decisive)} source(s) that took a position support the statement "
                              f"(weighted by how reliable each source is).",
                })
            elif kind in ("factcheck", "news"):
                sections.append({
                    "key": kind, "title": title, "percent": None, "status": "unknown",
                    "detail": f"{what} Nothing found in this group took a clear position, so it does not move the score.",
                })

        # Forensic sections (images, video, audio)
        for d in (detector_details or []):
            risk = d.get("risk")
            if risk is None:
                pct = None
            else:
                pct = round(min(max(100.0 - float(risk), 2.0), 88.0), 0)
            sections.append({
                "key": d.get("key", d["title"].lower().replace(" ", "_")),
                "title": d["title"], "percent": pct, "status": VerdictEngine._status(pct),
                "detail": d.get("detail", ""),
            })

        letter, label = VerdictEngine._grade(correctness_score)
        has_claim = any(sec["key"] in ("factcheck", "knowledge", "news") for sec in sections)
        has_media = bool(detector_details)
        if ai_analysis and ai_analysis.get("truth_percent") is not None:
            how = ("The overall percentage is Google Gemini's assessment of how likely the statement is to be factually true. "
                   "The rows below show Gemini's rating of each aspect (higher is better), followed by what the "
                   "fact-checker and news searches found, which are shown for comparison.")
        elif has_claim and has_media:
            how = "The overall percentage is the lower of the claim result and the media result, because both must be right."
        elif has_media:
            how = ("The overall percentage is 100 minus the strongest warning score from the checks in this card, capped at 88% "
                   "because software can find signs of AI or editing but can never prove a file is untouched.")
        else:
            how = ("The overall percentage is the share of reliable evidence that supports the statement, pulled toward 50% "
                   "when there is no fact-check or reference record to anchor it.")

        caveats = [
            "This is an automated estimate, not a guarantee. Treat anything below about 70% or above about 30% as a reason to check further.",
            "Every test above only looks at the information available to it; a test marked \"no result\" was not able to judge and did not affect the percentage.",
        ]
        if has_media:
            caveats.append("The built-in image/audio/video tests are statistical heuristics. Modern AI media can pass them, "
                           "so a high percentage means \"no warning signs found\", not \"proven real\".")

        return {
            "overall_percent": correctness_score,
            "grade": letter,
            "grade_label": label,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "sections": sections,
            "how_calculated": how,
            "explanation": correctness_explanation,
            "caveats": caveats,
        }

    @staticmethod
    def synthesize_overall_verdict(
        input_type: str,
        factual_verdict: Optional[str],
        media_verdict: Optional[str],
        context_verdict: Optional[str],
        evidence_items: List[Dict[str, Any]],
        detector_scores: List[float],
        indicators: List[str],
        summary_hint: str = "",
        detector_details: Optional[List[Dict[str, Any]]] = None,
        ai_analysis: Optional[Dict[str, Any]] = None
    ) -> VerdictSynthesis:
        """Combines the 3 pillars into a simple, user-friendly final verdict with high clarity."""
        conf_score, conf_level, conf_explanation = calculate_system_confidence(
            evidence_items=evidence_items,
            detector_scores=detector_scores
        )

        if ai_analysis and input_type in ("claim", "url"):
            g_conf = float(ai_analysis.get("confidence_percent", 50))
            conf_score = round(min(max(g_conf, 10.0), 95.0), 1)
            conf_level = (ConfidenceLevel.HIGH if conf_score >= 75 else
                          ConfidenceLevel.MEDIUM if conf_score >= 50 else ConfidenceLevel.LOW)
            conf_explanation = f"{conf_level.value.title()} confidence ({conf_score}%): Gemini rated how sure it is of this assessment."

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
                    summary = "This media shows signs of editing or splicing, such as compression mismatches."
            elif media_verdict == MediaAuthenticityType.SUSPICIOUS_ARTIFACTS.value:
                overall_verdict = "SUSPICIOUS"
                verdict_label = "Suspicious Edits Detected"
                summary = "This file shows editing signals (for example an editing-software tag or borderline artifacts). Editing alone does not mean it is fake, but check where it came from."
            elif media_verdict in (MediaAuthenticityType.AUTHENTIC.value, MediaAuthenticityType.LIKELY_AUTHENTIC.value):
                if context_verdict == ContextVerdictType.MISLEADING_CONTEXT.value:
                    overall_verdict = "MISLEADING_CONTEXT"
                    verdict_label = "Real Media, Fake Story (Wrong Context)"
                    summary = "The image or video is a genuine camera capture, but it is being recycled or described with a false caption/date."
                else:
                    overall_verdict = "AUTHENTIC"
                    verdict_label = "Likely Real (No Manipulation Found)"
                    summary = "The automated tests found no signs of AI generation or editing. This lowers the risk but cannot prove the file is genuine."
            else:
                overall_verdict = "INCONCLUSIVE"
                verdict_label = "Inconclusive / Low Quality"
                summary = "The file resolution or quality is too low to definitively confirm authenticity or manipulation."

        correctness_score, correctness_explanation = VerdictEngine.estimate_correctness(
            input_type, evidence_items, detector_scores, media_verdict, conf_score
        )

        if ai_analysis and ai_analysis.get("truth_percent") is not None:
            correctness_score = float(ai_analysis["truth_percent"])
            correctness_explanation = (
                f"Gemini ({ai_analysis.get('model', 'AI')}) rates this statement {correctness_score:.0f}% likely to be true. "
                + (ai_analysis.get("explanation") or "")
            ).strip()
            if ai_analysis.get("summary"):
                summary = ai_analysis["summary"]
        if ai_analysis and input_type in ("claim", "url") and ai_analysis.get("truth_percent") is None and ai_analysis.get("summary"):
            summary = ai_analysis["summary"]

        report_card = VerdictEngine.build_report_card(
            input_type, evidence_items, detector_details, correctness_score,
            correctness_explanation, conf_score, conf_level.value, ai_analysis=ai_analysis
        )

        # Build comprehensive readable explanation in plain English
        explanation_parts = [
            f"**Quick Summary**: {summary}",
            f"\n\n**Confidence Level**: {conf_score}% certainty ({conf_explanation})",
            "\n\n**Three-Point Check Breakdown**:"
        ]
        if ai_analysis:
            pct_txt = "no percentage" if ai_analysis.get("truth_percent") is None else f"{ai_analysis['truth_percent']:.0f}% likely true"
            explanation_parts.append(f"\n- **Gemini AI check**: {ai_analysis['verdict'].replace('_', ' ').title()} ({pct_txt}). {ai_analysis.get('explanation', '')}")
            for kp in ai_analysis.get("key_points", []):
                tag = {"supports": "supports", "contradicts": "contradicts"}.get(kp["assessment"], "context")
                explanation_parts.append(f"\n  - ({tag}) {kp['point']}")
        if factual_verdict:
            simple_fact = factual_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **1. Fact Check**: {simple_fact} — Based on {len(evidence_items)} referenced fact-check and encyclopedia sources.")
        if media_verdict:
            simple_media = media_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **2. Media Authenticity**: {simple_media} — Analyzed using metadata, noise distribution and frequency scans.")
        if context_verdict:
            simple_context = context_verdict.replace('_', ' ').title()
            explanation_parts.append(f"\n- **3. Context & Caption**: {simple_context} — Verified against recording timestamps and event history.")

        if evidence_items:
            explanation_parts.append("\n\n**Sources Reviewed and How They Affected the Score**:")
            for item in evidence_items[:8]:
                stance = item.get("stance", "NEUTRAL")
                effect = {"SUPPORTS": "supports the claim", "CONTRADICTS": "contradicts the claim"}.get(stance, "background only, not counted")
                explanation_parts.append(f"\n- {item.get('publisher') or item.get('source_name')} (reliability {item.get('credibility_score', 0):.0f}/100): {effect}.")
        elif input_type in ("claim", "url"):
            explanation_parts.append("\n\n**Sources Reviewed**: none returned usable evidence, so no verdict is claimed.")

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
            explanation=explanation,
            correctness_score=correctness_score,
            correctness_explanation=correctness_explanation,
            report_card=report_card
        )
