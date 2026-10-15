from typing import List, Dict, Any
from app.engines.news.claim_extractor import extract_claims_from_text


class ClaimExtractorService:
    @staticmethod
    def extract_verifiable_claims(text: str, max_claims: int = 5) -> List[Dict[str, Any]]:
        return extract_claims_from_text(text, max_claims=max_claims)
