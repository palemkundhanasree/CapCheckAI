from typing import List, Dict, Any, Tuple
from app.config import settings
from app.engines.news.claim_matcher import match_and_score_evidence
from app.engines.news.factcheck_client import search_curated_factchecks, query_google_factcheck_api
from app.engines.news.knowledge_checker import check_entity_type_claim
from app.engines.news.search_client import search_web_evidence, search_news_coverage


class EvidenceEvaluatorService:
    @staticmethod
    def evaluate_and_rank_evidence(claim_text: str, raw_evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates, scores lexical overlap, and sorts evidence by reliability and stance."""
        seen_keys = set()
        deduped = []
        for item in raw_evidence:
            key = item.get("source_url") or item.get("title", "")
            if key and key not in seen_keys:
                seen_keys.add(key)
                deduped.append(item)
        return match_and_score_evidence(claim_text, deduped)


async def gather_claim_evidence(claim: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Collects real evidence for a claim from every available source and reports which
    checks could not run, so the result never implies a source was consulted when it was not.
    """
    unavailable: List[str] = []
    evidence: List[Dict[str, Any]] = []

    evidence.extend(await check_entity_type_claim(claim))
    evidence.extend(search_curated_factchecks(claim))

    if settings.GOOGLE_FACTCHECK_API_KEY:
        evidence.extend(await query_google_factcheck_api(claim))
    else:
        unavailable.append("Google Fact Check Tools API (no API key configured)")

    news, notes = await search_news_coverage(claim)
    evidence.extend(news)
    unavailable.extend(notes)

    evidence.extend(await search_web_evidence(claim))
    return EvidenceEvaluatorService.evaluate_and_rank_evidence(claim, evidence), unavailable
