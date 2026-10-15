from typing import Dict, Any, List
from app.engines.news.claim_extractor import extract_claims_from_text
from app.engines.news.factcheck_client import search_curated_factchecks, query_google_factcheck_api
from app.engines.news.search_client import search_web_evidence
from app.engines.news.claim_matcher import match_and_score_evidence


async def check_speech_factual_claims(transcript: str) -> Dict[str, Any]:
    """
    Extracts verifiable claims from audio transcript and collects evidence.
    """
    if not transcript or len(transcript.strip()) < 10:
        return {
            "claims_found": [],
            "evidence": [],
            "claim_verdict": "INCONCLUSIVE"
        }

    claims = extract_claims_from_text(transcript, max_claims=3)
    primary_claim = claims[0]["claim_text"] if claims else transcript[:150]

    # Gather evidence
    evidence = []
    # 1. Curated fact checks
    curated = search_curated_factchecks(primary_claim)
    evidence.extend(curated)

    # 2. Google Fact Check API
    api_hits = await query_google_factcheck_api(primary_claim)
    evidence.extend(api_hits)

    # 3. Wikipedia / web search
    if len(evidence) < 2:
        wiki_hits = await search_web_evidence(primary_claim)
        evidence.extend(wiki_hits)

    scored_evidence = match_and_score_evidence(primary_claim, evidence)

    # Determine claim verdict
    contradicting = sum(1 for e in scored_evidence if e["stance"] == "CONTRADICTS")
    supporting = sum(1 for e in scored_evidence if e["stance"] == "SUPPORTS")

    if contradicting > supporting:
        verdict = "CONTRADICTED"
    elif supporting > contradicting:
        verdict = "SUPPORTED"
    elif scored_evidence:
        verdict = "MISLEADING_CONTEXT"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "primary_claim": primary_claim,
        "claims_found": [c["claim_text"] for c in claims],
        "evidence": scored_evidence,
        "claim_verdict": verdict
    }
