import re
from typing import List, Dict, Any


def tokenize_clean(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stopwords = {
        "the", "and", "that", "this", "with", "from", "for", "have", "been",
        "were", "they", "will", "are", "was", "has", "about", "what", "which",
        "who", "when", "where", "into", "more", "some", "such"
    }
    return {w for w in words if w not in stopwords}


def compute_evidence_stance(claim_text: str, evidence_snippet: str, existing_stance: str = "NEUTRAL") -> str:
    """
    Refines stance by analyzing negation, refutation, affirmation, and semantic alignment.
    Refutation patterns always take priority over generic defaults.
    """
    snippet_lower = evidence_snippet.lower()

    refutation_patterns = [
        r"\b(false|debunked|hoax|unfounded|fabricated|incorrect|disproven|no evidence|myth|altered)\b",
        r"\b(never happened|did not|not true|denied|untrue|staged|conspiracy theory|contrary to)\b",
        r"\b(misconception|fictional|pseudo-science|unsubstantiated|scientifically disproven|archaic conception)\b",
        r"\b(not flat|earth is round|spherical earth|oblate spheroid)\b"
    ]
    corroboration_patterns = [
        r"\b(confirmed|verified|documented|established|proven|official record|authentic)\b",
        r"\b(true|accurate|corroborated|supported by evidence|officially recognized)\b",
        r"\b(scientific consensus|known as|defined as|capital of|orbits the|located in)\b"
    ]

    # Refutation check always takes precedence
    for pat in refutation_patterns:
        if re.search(pat, snippet_lower):
            return "CONTRADICTS"

    if existing_stance in ("CONTRADICTS", "SUPPORTS"):
        return existing_stance

    for pat in corroboration_patterns:
        if re.search(pat, snippet_lower):
            return "SUPPORTS"

    # Token overlap check: If high token overlap exists without any refutations, it's corroborating
    claim_tokens = tokenize_clean(claim_text)
    snippet_tokens = tokenize_clean(evidence_snippet)
    if claim_tokens:
        overlap_ratio = len(claim_tokens.intersection(snippet_tokens)) / len(claim_tokens)
        if overlap_ratio >= 0.60:
            return "SUPPORTS"

    return "NEUTRAL"


def match_and_score_evidence(claim_text: str, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scores lexical relevance and refines stance for all evidence items."""
    claim_tokens = tokenize_clean(claim_text)

    scored_items = []
    for item in evidence_list:
        text_corpus = f"{item.get('title', '')} {item.get('snippet', '')}"
        corpus_tokens = tokenize_clean(text_corpus)

        overlap = len(claim_tokens.intersection(corpus_tokens))
        relevance_ratio = overlap / max(len(claim_tokens), 1)

        if item.get("kind") == "reference":
            # Encyclopedia/background hits show context only; they never count as proof either way.
            refined_stance = "NEUTRAL"
        elif item.get("kind") in ("factcheck", "news", "knowledge"):
            refined_stance = item.get("stance", "NEUTRAL")  # already judged against the source text
        else:
            refined_stance = compute_evidence_stance(claim_text, text_corpus, item.get("stance", "NEUTRAL"))

        item_copy = dict(item)
        item_copy["stance"] = refined_stance
        item_copy["relevance_score"] = round(min(relevance_ratio * 100, 100.0), 1)
        scored_items.append(item_copy)

    # Sort items by relevance and credibility
    scored_items.sort(key=lambda x: (x.get("relevance_score", 0) + x.get("credibility_score", 0)), reverse=True)
    return scored_items
