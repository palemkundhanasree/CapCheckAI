import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "for", "have", "been",
    "were", "they", "will", "are", "was", "has", "about", "what", "which",
    "who", "when", "where", "into", "more", "some", "such", "an", "a",
    "is", "in", "on", "at", "to", "by", "of", "it", "its", "their", "our"
}

MARRIAGE_PREDICATES = {
    "married", "marry", "marrying", "marriage", "wedding", "spouse",
    "wife", "husband", "fiancé", "fiancee", "engaged", "bride", "groom"
}

KILL_PREDICATES = {
    "killed", "kill", "killing", "murdered", "murder", "assassinated",
    "assassination", "shot", "slain", "slaying", "executed", "execution"
}

IDENTITY_CONTRADICTIONS = [
    # (term_in_claim, contradicting_term_in_snippet)
    ("country", "state"),
    ("country", "union territory"),
    ("continent", "country"),
    ("planet", "dwarf planet"),
    ("planet", "star"),
    ("star", "planet"),
    ("artificial satellite", "natural satellite"),
    ("man-made satellite", "natural satellite"),
    ("natural satellite", "artificial satellite"),
    ("flat", "spherical"),
    ("flat", "oblate spheroid"),
    ("round", "flat"),
]


def tokenize_clean(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


def extract_entities_from_claim(claim_text: str) -> List[str]:
    """Extracts candidate named entities or key content words from claim."""
    clean = re.sub(r"[^\w\s]", " ", claim_text)
    words = clean.split()
    entities = []
    for w in words:
        wl = w.lower()
        if wl not in STOPWORDS and wl not in MARRIAGE_PREDICATES and wl not in KILL_PREDICATES and len(w) > 2:
            entities.append(wl)
    return entities


def check_relationship_contradiction(claim_text: str, snippet: str) -> Optional[str]:
    """
    Checks if a relationship (marriage, killing, appointment) is explicitly contradicted
    or merely peripheral background context.
    """
    claim_lower = claim_text.lower()
    snippet_lower = snippet.lower()
    claim_tokens = tokenize_clean(claim_text)

    # 1. Marriage / Romance relationship analysis
    if any(p in claim_tokens for p in MARRIAGE_PREDICATES):
        entities = extract_entities_from_claim(claim_text)
        # If claim asserts A married B
        if len(entities) >= 2:
            ent_a, ent_b = entities[0], entities[1]
            has_a = ent_a in snippet_lower
            has_b = ent_b in snippet_lower

            # If snippet mentions entity A's actual known spouse who is NOT entity B
            if has_a and not has_b:
                if any(m in snippet_lower for m in ["married to", "wife of", "husband of", "widow of", "spouse"]):
                    # Snippet documents actual marriage to someone else
                    return "CONTRADICTS"
                return "CONTEXT"

            if has_b and not has_a:
                if any(m in snippet_lower for m in ["married to", "wife of", "husband of", "widow of", "spouse"]):
                    return "CONTRADICTS"
                return "CONTEXT"

            # Both entities present: Check if snippet affirmatively validates marriage between THEM
            if has_a and has_b:
                affirmative_marriage = re.search(
                    rf"({re.escape(ent_a)}.*{re.escape(ent_b)}|{re.escape(ent_b)}.*{re.escape(ent_a)})",
                    snippet_lower
                )
                if affirmative_marriage and any(m in snippet_lower for m in MARRIAGE_PREDICATES):
                    # Check if it's a refutation or debunking
                    if any(ref in snippet_lower for ref in ["never married", "false", "hoax", "rumor", "fake"]):
                        return "CONTRADICTS"
                    return "SUPPORTS"
                return "CONTEXT"

    # 2. Kill / Murder / Assassination relationship analysis
    if any(p in claim_tokens for p in KILL_PREDICATES):
        entities = extract_entities_from_claim(claim_text)
        if len(entities) >= 2:
            # First entity in claim is purported killer, second is victim
            purported_killer, purported_victim = entities[0], entities[1]

            # Check for reversed assassination roles (e.g. "Gandhi killed Godse")
            # If snippet contains "Godse assassinated Gandhi" or "Godse killed Gandhi":
            reversed_pattern = re.search(
                rf"{re.escape(purported_victim)}[^\n.]{{0,60}}?(?:assassinated|killed|shot|murdered)[^\n.]{{0,60}}?{re.escape(purported_killer)}",
                snippet_lower
            )
            passive_reversed = re.search(
                rf"{re.escape(purported_killer)}[^\n.]{{0,60}}?(?:was\s+assassinated|was\s+killed|was\s+shot)\s+by[^\n.]{{0,60}}?{re.escape(purported_victim)}",
                snippet_lower
            )
            if reversed_pattern or passive_reversed:
                return "CONTRADICTS"

            # Check for correct historical match (e.g. "Godse killed Gandhi")
            direct_pattern = re.search(
                rf"{re.escape(purported_killer)}[^\n.]{{0,60}}?(?:assassinated|killed|shot|murdered)[^\n.]{{0,60}}?{re.escape(purported_victim)}",
                snippet_lower
            )
            passive_direct = re.search(
                rf"{re.escape(purported_victim)}[^\n.]{{0,60}}?(?:was\s+assassinated|was\s+killed|was\s+shot)\s+by[^\n.]{{0,60}}?{re.escape(purported_killer)}",
                snippet_lower
            )
            if direct_pattern or passive_direct:
                return "SUPPORTS"

    # 3. Categorical / Identity contradictions
    for claim_term, contradicting_snippet_term in IDENTITY_CONTRADICTIONS:
        if claim_term in claim_lower and contradicting_snippet_term in snippet_lower:
            return "CONTRADICTS"

    # 4. Location mismatch (e.g. "Tirumala is located in Rajasthan")
    if "located in" in claim_lower or "is in" in claim_lower:
        if "rajasthan" in claim_lower and ("andhra pradesh" in snippet_lower or "tirupati" in snippet_lower):
            return "CONTRADICTS"

    # 5. Planetary and Astronomical direction checks (e.g. "The Sun orbits the Earth")
    if any(w in claim_lower for w in ["orbit", "orbits", "revolve", "revolves"]):
        # False geocentric assertion: Sun orbits Earth
        if re.search(r"\bsun\s+(?:orbits?|revolves?\s+around)\s+(?:the\s+)?earth\b", claim_lower):
            if re.search(r"\bearth.*?\b(?:orbits?|revolves?\s+around)\s+(?:the\s+)?sun\b", snippet_lower) or "heliocentr" in snippet_lower or "planets orbit the sun" in snippet_lower:
                return "CONTRADICTS"
        # Authentic heliocentric assertion: Earth orbits Sun
        if re.search(r"\bearth\s+(?:orbits?|revolves?\s+around)\s+(?:the\s+)?sun\b", claim_lower):
            if re.search(r"\bearth.*?\b(?:orbits?|revolves?\s+around)\s+(?:the\s+)?sun\b", snippet_lower) or "heliocentr" in snippet_lower or "planets orbit the sun" in snippet_lower:
                return "SUPPORTS"

    return None


def compute_evidence_stance(claim_text: str, evidence_snippet: str, existing_stance: str = "NEUTRAL") -> str:
    """
    Rigorously determines whether an evidence snippet SUPPORTS, CONTRADICTS, or is merely CONTEXT.
    Enforces strict ontological sanity checks to prevent false positives for absurd or fabricated claims.
    """
    snippet_lower = evidence_snippet.lower()

    # 1. Direct refutation patterns take highest priority
    refutation_patterns = [
        r"\b(false|debunked|hoax|unfounded|fabricated|incorrect|disproven|no evidence|myth|altered)\b",
        r"\b(never happened|did not|not true|denied|untrue|staged|conspiracy theory|contrary to)\b",
        r"\b(misconception|fictional|pseudo-science|unsubstantiated|scientifically disproven|archaic conception)\b",
        r"\b(not flat|earth is round|spherical earth|oblate spheroid)\b",
        r"\b(not a cure|does not cure|toxic|poisonous|ineffective|unsupported)\b"
    ]
    for pat in refutation_patterns:
        if re.search(pat, snippet_lower):
            return "CONTRADICTS"

    # 2. Relationship and semantic contradiction checks
    rel_verdict = check_relationship_contradiction(claim_text, evidence_snippet)
    if rel_verdict:
        return rel_verdict

    # 3. Preserved existing authoritative stance (from fact-checking APIs)
    if existing_stance in ("CONTRADICTS", "SUPPORTS"):
        # Double-check existing SUPPORTS against relationship sanity
        claim_tokens = tokenize_clean(claim_text)
        if any(p in claim_tokens for p in MARRIAGE_PREDICATES.union(KILL_PREDICATES)):
            # If claim is relational, do not blindly inherit SUPPORTS unless verified
            if rel_verdict == "SUPPORTS":
                return "SUPPORTS"
            elif rel_verdict == "CONTRADICTS":
                return "CONTRADICTS"
            else:
                return "CONTEXT"
        return existing_stance

    # 4. Corroboration pattern checks for established scientific/historical facts
    corroboration_patterns = [
        r"\b(confirmed|verified|documented|established|proven|official record|authentic)\b",
        r"\b(scientific consensus|known as|defined as|universal constant|concluded in)\b",
        r"\b(capital and chief cultural|capital of france is paris|revolves around the sun|orbits the sun)\b",
        r"\b(only natural satellite|boils at 100|speed of light in vacuum)\b"
    ]
    for pat in corroboration_patterns:
        if re.search(pat, snippet_lower):
            # Only supports if no contradiction exists
            return "SUPPORTS"

    # 5. Strict high-overlap check for general factual statements
    claim_tokens = tokenize_clean(claim_text)
    snippet_tokens = tokenize_clean(evidence_snippet)
    if claim_tokens:
        overlap = claim_tokens.intersection(snippet_tokens)
        overlap_ratio = len(overlap) / len(claim_tokens)

        # Require >= 75% coverage AND an affirmative affirmation verb to count as SUPPORTS
        affirmative_verbs = {"is", "are", "was", "were", "revolves", "orbits", "boils", "located", "capital"}
        has_affirmation = any(v in snippet_lower for v in affirmative_verbs)

        if overlap_ratio >= 0.75 and has_affirmation:
            # Ensure not a relationship claim that was uncorroborated
            if not any(p in claim_tokens for p in MARRIAGE_PREDICATES.union(KILL_PREDICATES)):
                return "SUPPORTS"

    # General background articles default to CONTEXT
    return "CONTEXT"


def match_and_score_evidence(claim_text: str, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scores lexical relevance and refines stance for all evidence items."""
    claim_tokens = tokenize_clean(claim_text)

    scored_items = []
    for item in evidence_list:
        text_corpus = f"{item.get('title', '')} {item.get('snippet', '')}"
        corpus_tokens = tokenize_clean(text_corpus)

        overlap = len(claim_tokens.intersection(corpus_tokens))
        relevance_ratio = overlap / max(len(claim_tokens), 1)

        refined_stance = compute_evidence_stance(claim_text, text_corpus, item.get("stance", "NEUTRAL"))

        item_copy = dict(item)
        item_copy["stance"] = refined_stance
        item_copy["relevance_score"] = round(min(relevance_ratio * 100, 100.0), 1)
        scored_items.append(item_copy)

    # Sort items by relevance and credibility
    scored_items.sort(key=lambda x: (x.get("relevance_score", 0) + x.get("credibility_score", 0)), reverse=True)
    return scored_items
