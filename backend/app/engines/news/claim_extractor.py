import re
from typing import List, Dict, Any


def extract_claims_from_text(text: str, max_claims: int = 5) -> List[Dict[str, Any]]:
    """
    Extracts distinct verifiable factual statements, identifying numeric claims,
    entity mentions, and high-assertion statements.
    """
    if not text:
        return []

    # Clean text and split into sentences
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    # Sentence splitting regex respecting common abbreviations
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned_text)

    # Patterns indicating verifiable factual assertion
    claim_indicators = [
        re.compile(r"\b(stated|claimed|announced|discovered|banned|approved|died|killed|signed|passed)\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?%|\$\d+|\d{4}|\bmillion\b|\bbillion\b|\bpercent\b)\b", re.I),
        re.compile(r"\b(caused by|proven to|cure for|evidence shows|confirmed|first ever|record high|record low)\b", re.I),
        re.compile(r"\b(according to|study finds|report reveals|investigation)\b", re.I)
    ]

    claims = []
    for sentence in raw_sentences:
        s = sentence.strip()
        if len(s) < 20 or len(s) > 300:
            continue

        # Score statement for fact-checkability
        score = 0
        matches = []
        for pat in claim_indicators:
            m = pat.findall(s)
            if m:
                score += len(m) * 2
                matches.extend(m)

        # Look for capitalised named entities (approximate)
        named_entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", s)
        score += min(len(named_entities), 3)

        if score >= 2 or len(raw_sentences) <= 3:
            claims.append({
                "claim_text": s,
                "importance_score": score,
                "entities": named_entities[:4],
                "keywords": [str(m).lower() for m in matches[:3]]
            })

    # Sort by importance and take top claims
    claims.sort(key=lambda x: x["importance_score"], reverse=True)
    return claims[:max_claims] if claims else [{"claim_text": text[:200], "importance_score": 1, "entities": [], "keywords": []}]
