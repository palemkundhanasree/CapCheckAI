from typing import List, Dict, Any
from app.engines.news.claim_matcher import match_and_score_evidence


class EvidenceEvaluatorService:
    @staticmethod
    def evaluate_and_rank_evidence(claim_text: str, raw_evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates, scores lexical overlap, and sorts evidence by reliability and stance.
        """
        # Deduplicate by URL or title
        seen_keys = set()
        deduped = []
        for item in raw_evidence:
            key = item.get("source_url") or item.get("title", "")
            if key and key not in seen_keys:
                seen_keys.add(key)
                deduped.append(item)

        return match_and_score_evidence(claim_text, deduped)
