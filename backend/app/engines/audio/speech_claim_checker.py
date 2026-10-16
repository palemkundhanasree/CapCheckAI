from typing import Dict, Any
from app.engines.news.claim_extractor import extract_claims_from_text


async def check_speech_factual_claims(transcript: str) -> Dict[str, Any]:
    """Extracts verifiable claims from a transcript and collects real evidence for the main one."""
    from app.services.evidence_evaluator import gather_claim_evidence
    from app.services.verdict_engine import VerdictEngine

    if not transcript or len(transcript.strip()) < 10:
        return {"claims_found": [], "evidence": [], "claim_verdict": None, "unavailable": []}

    claims = extract_claims_from_text(transcript, max_claims=3)
    primary_claim = claims[0]["claim_text"] if claims else transcript[:200]
    evidence, unavailable = await gather_claim_evidence(primary_claim)
    return {
        "primary_claim": primary_claim,
        "claims_found": [c["claim_text"] for c in claims],
        "evidence": evidence,
        "claim_verdict": VerdictEngine.evaluate_claim_verdict(evidence),
        "unavailable": unavailable,
    }
