import re
from typing import List, Dict, Any

OPINION_PATTERNS = [
    re.compile(r"\b(in my opinion|i think|i believe|i feel|in our view|to my mind|in my eyes)\b", re.I),
    re.compile(r"\b(is the best|is the worst|is the greatest|is the finest|most beautiful|ugliest)\b", re.I),
    re.compile(r"\b(delicious|tasty|boring|fun|awesome|horrible|wonderful|overrated|underrated)\b", re.I),
    re.compile(r"\b(should be|ought to be|deserves to be|my favorite|our favorite)\b", re.I),
]


def is_subjective_opinion(text: str) -> bool:
    """Detects subjective commentary, personal tastes, and value judgments."""
    t = text.strip()
    for pat in OPINION_PATTERNS:
        if pat.search(t):
            # Check if it also has empirical numbers/dates/laws that make it factual
            has_hard_data = re.search(r"(\d+(?:\.\d+)?%|\$\d+|\b\d{4}\b|km/s|degrees celsius)", t, re.I)
            if not has_hard_data:
                return True
    return False


def split_compound_claim(text: str) -> List[str]:
    """Splits compound sentences joined by contrasting or additive conjunctions."""
    t = text.strip()
    # Check for compound conjunctions: " and ", " but ", " while "
    parts = re.split(r"\s+(?:and|but|while)\s+(?=[a-z0-9\s]{10,})", t, flags=re.I)
    cleaned = [p.strip().rstrip(".,;!?") for p in parts if len(p.strip().split()) >= 3]
    return cleaned if len(cleaned) > 1 else [t]


def extract_claims_from_text(text: str, max_claims: int = 5) -> List[Dict[str, Any]]:
    """
    Extracts distinct verifiable factual statements, identifying numeric claims,
    entity mentions, subjective opinions, and compound claims.
    """
    if not text:
        return []

    # Clean text and split into sentences
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned_text)

    claim_indicators = [
        re.compile(r"\b(stated|claimed|announced|discovered|banned|approved|died|killed|signed|passed)\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?%|\$\d+|\d{4}|\bmillion\b|\bbillion\b|\bpercent\b)\b", re.I),
        re.compile(r"\b(caused by|proven to|cure for|evidence shows|confirmed|first ever|record high|record low)\b", re.I),
        re.compile(r"\b(according to|study finds|report reveals|investigation)\b", re.I),
        re.compile(r"\b(orbits|revolves|boils|speed of light|capital of|located in)\b", re.I)
    ]

    claims = []

    # Process all sentences, decomposing compound sentences if present
    for sentence in raw_sentences:
        s = sentence.strip()
        if len(s) < 10 or len(s) > 400:
            continue

        sub_parts = split_compound_claim(s)

        for part in sub_parts:
            # Check for subjective opinion
            is_opinion = is_subjective_opinion(part)

            score = 0
            matches = []
            for pat in claim_indicators:
                m = pat.findall(part)
                if m:
                    score += len(m) * 2
                    matches.extend(m)

            named_entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", part)
            score += min(len(named_entities), 3)

            claims.append({
                "claim_text": part,
                "importance_score": score,
                "is_opinion": is_opinion,
                "entities": named_entities[:4],
                "keywords": [str(m).lower() for m in matches[:3]]
            })

    # Sort by importance and take top claims
    claims.sort(key=lambda x: (not x["is_opinion"], x["importance_score"]), reverse=True)
    return claims[:max_claims] if claims else [{
        "claim_text": text[:200],
        "importance_score": 1,
        "is_opinion": is_subjective_opinion(text),
        "entities": [],
        "keywords": []
    }]
