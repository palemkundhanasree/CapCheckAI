"""
Checks "X is a Y" claims (for example "Andhra Pradesh is a country") against reference knowledge.

Why this exists: simple word matching cannot tell "Andhra Pradesh is a state" from "Andhra Pradesh is a
country" because both share the same words. Here the claim is split into a subject and a category and the
category is compared with what reference sources say the subject actually is.
"""
import difflib
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand", "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
    "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal",
}
INDIAN_UTS = {
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli and daman and diu", "delhi",
    "jammu and kashmir", "ladakh", "lakshadweep", "puducherry",
}
COUNTRIES = {
    "afghanistan", "albania", "algeria", "andorra", "angola", "antigua and barbuda", "argentina", "armenia",
    "australia", "austria", "azerbaijan", "bahamas", "bahrain", "bangladesh", "barbados", "belarus", "belgium",
    "belize", "benin", "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil", "brunei", "bulgaria",
    "burkina faso", "burundi", "cambodia", "cameroon", "canada", "cape verde", "central african republic",
    "chad", "chile", "china", "colombia", "comoros", "congo", "costa rica", "croatia", "cuba", "cyprus",
    "czech republic", "czechia", "denmark", "djibouti", "dominica", "dominican republic", "ecuador", "egypt",
    "el salvador", "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia", "fiji", "finland",
    "france", "gabon", "gambia", "georgia", "germany", "ghana", "greece", "grenada", "guatemala", "guinea",
    "guinea-bissau", "guyana", "haiti", "honduras", "hungary", "iceland", "india", "indonesia", "iran", "iraq",
    "ireland", "israel", "italy", "ivory coast", "jamaica", "japan", "jordan", "kazakhstan", "kenya",
    "kiribati", "kosovo", "kuwait", "kyrgyzstan", "laos", "latvia", "lebanon", "lesotho", "liberia", "libya",
    "liechtenstein", "lithuania", "luxembourg", "madagascar", "malawi", "malaysia", "maldives", "mali", "malta",
    "marshall islands", "mauritania", "mauritius", "mexico", "micronesia", "moldova", "monaco", "mongolia",
    "montenegro", "morocco", "mozambique", "myanmar", "namibia", "nauru", "nepal", "netherlands",
    "new zealand", "nicaragua", "niger", "nigeria", "north korea", "north macedonia", "norway", "oman",
    "pakistan", "palau", "palestine", "panama", "papua new guinea", "paraguay", "peru", "philippines", "poland",
    "portugal", "qatar", "romania", "russia", "rwanda", "saint kitts and nevis", "saint lucia",
    "saint vincent and the grenadines", "samoa", "san marino", "sao tome and principe", "saudi arabia",
    "senegal", "serbia", "seychelles", "sierra leone", "singapore", "slovakia", "slovenia", "solomon islands",
    "somalia", "south africa", "south korea", "south sudan", "spain", "sri lanka", "sudan", "suriname", "sweden",
    "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand", "timor-leste", "togo", "tonga",
    "trinidad and tobago", "tunisia", "turkey", "turkmenistan", "tuvalu", "uganda", "ukraine",
    "united arab emirates", "united kingdom", "united states", "uruguay", "uzbekistan", "vanuatu",
    "vatican city", "venezuela", "vietnam", "yemen", "zambia", "zimbabwe",
}

COUNTRY_WORDS = {"country", "nation", "sovereign state", "sovereign country", "independent country", "independent nation"}
SUBNATIONAL_WORDS = {"state", "province", "union territory", "territory", "region", "district", "city", "town",
                     "village", "county", "prefecture", "municipality", "capital city"}
CATEGORY_VOCAB = COUNTRY_WORDS | SUBNATIONAL_WORDS | {"continent", "river", "mountain", "lake", "island", "planet",
                                                    "ocean", "sea", "star", "desert", "company", "language"}

_ARTICLES = r"(?:an?|the)"
IS_A_PATTERN = re.compile(
    rf"^(?:is it true that\s+|it is said that\s+)?(?:the\s+)?(?P<subj>[A-Za-z][A-Za-z .'\-]{{1,60}}?)\s+"
    rf"(?:is|are|was|were)\s+(?P<neg>not\s+|never\s+)?(?:{_ARTICLES}\s+)?(?P<pred>[A-Za-z][A-Za-z \-]{{2,40}})$",
    re.IGNORECASE,
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 \-]", " ", s.lower())).strip()


def parse_is_a_claim(claim: str) -> Optional[Dict[str, Any]]:
    """Splits "Andhra Pradesh is a country" into subject / category / negation, or returns None."""
    text = re.sub(r"\s+", " ", claim.strip().rstrip(".!?"))
    m = IS_A_PATTERN.match(text)
    if not m:
        return None
    pred = re.split(r"\b(?:in|of|located|situated|within|which|that|with|and)\b", m.group("pred"), maxsplit=1,
                    flags=re.IGNORECASE)[0].strip().lower()
    pred = re.sub(r"^(?:an?|the)\s+", "", pred)
    if not pred:
        return None
    # Singularise very common plural slips ("states" -> "state")
    if pred.endswith("ies"):
        pred = pred[:-3] + "y"
    elif pred.endswith("s") and pred[:-1] in CATEGORY_VOCAB:
        pred = pred[:-1]
    return {"subject": m.group("subj").strip(), "category": pred, "negated": bool(m.group("neg"))}


def _same_group(a: str, b: str) -> Optional[bool]:
    """True if both words mean the same kind of place, False if they clearly differ, None if unknown."""
    if a in COUNTRY_WORDS and b in COUNTRY_WORDS:
        return True
    if a in SUBNATIONAL_WORDS and b in SUBNATIONAL_WORDS:
        # a state is not a city, but state/province/territory/region are all the "same" administrative level
        admin = {"state", "province", "union territory", "territory", "region", "prefecture"}
        if a == b or (a in admin and b in admin):
            return True
        return False
    if a in CATEGORY_VOCAB and b in CATEGORY_VOCAB:
        return False
    return None


def _verdict_for(claimed: str, actual: str, negated: bool) -> Optional[str]:
    """Returns SUPPORTS / CONTRADICTS for the claim, or None when the comparison is not meaningful."""
    same = _same_group(claimed, actual)
    if same is None:
        return None
    # "X is a state" about a sovereign country is a loose use of the word, so it is not scored
    if claimed in SUBNATIONAL_WORDS and actual in COUNTRY_WORDS:
        return None
    result = "SUPPORTS" if same else "CONTRADICTS"
    if negated:
        result = "CONTRADICTS" if result == "SUPPORTS" else "SUPPORTS"
    return result


def _local_lookup(subject: str) -> Optional[Dict[str, str]]:
    name = _norm(subject)
    for table, kind, where in (
        (INDIAN_STATES, "state", "a state of India"),
        (INDIAN_UTS, "union territory", "a union territory of India"),
        (COUNTRIES, "country", "a sovereign country"),
    ):
        if name in table:
            return {"kind": kind, "name": name, "where": where}
        close = difflib.get_close_matches(name, list(table), n=1, cutoff=0.86)  # tolerates spelling slips
        if close:
            return {"kind": kind, "name": close[0], "where": where}
    return None


def _evidence(title: str, source: str, url: str, snippet: str, stance: str, cred: float) -> Dict[str, Any]:
    return {
        "title": title, "source_name": source, "source_url": url, "publisher": source, "publish_date": "",
        "snippet": snippet, "stance": stance, "credibility_score": cred, "kind": "knowledge",
    }


async def _wikipedia_description(subject: str) -> Optional[Dict[str, str]]:
    headers = {"User-Agent": "CapCheck-AI/1.0 (verification)"}
    try:
        async with httpx.AsyncClient(timeout=6.0, headers=headers, follow_redirects=True) as client:
            r = await client.get("https://en.wikipedia.org/w/api.php", params={
                "action": "opensearch", "search": subject, "limit": 1, "format": "json"})
            if r.status_code != 200:
                return None
            data = r.json()
            if not data[1]:
                return None
            title = data[1][0]
            s = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}")
            if s.status_code != 200:
                return None
            j = s.json()
            return {"title": j.get("title", title), "description": (j.get("description") or "").lower(),
                    "extract": j.get("extract", ""), "url": j.get("content_urls", {}).get("desktop", {}).get("page", "")}
    except Exception as e:
        logger.debug(f"Wikipedia lookup failed: {e}")
        return None


def _head_category(description: str) -> str:
    head = re.split(r"\b(?:in|of|located|within|on|at|from)\b|[,;(]", description, maxsplit=1)[0].strip()
    head = re.sub(r"^(?:the|an?|sovereign|independent|federated|federal|constituent)\s+", "", head).strip()
    for word in sorted(CATEGORY_VOCAB, key=len, reverse=True):
        if head == word or head.endswith(" " + word):
            return word
    return head


async def check_entity_type_claim(claim: str) -> List[Dict[str, Any]]:
    """Returns decisive evidence for "X is a Y" claims. Returns [] when the claim is not of that form."""
    parsed = parse_is_a_claim(claim)
    if not parsed or parsed["category"] not in CATEGORY_VOCAB:
        return []
    subject, claimed, negated = parsed["subject"], parsed["category"], parsed["negated"]
    items: List[Dict[str, Any]] = []

    local = _local_lookup(subject)
    if local:
        stance = _verdict_for(claimed, local["kind"], negated)
        if stance:
            nice = local["name"].title()
            items.append(_evidence(
                f"{nice} is {local['where']}",
                "Built-in reference list (states, union territories and sovereign countries)",
                "https://en.wikipedia.org/wiki/States_and_union_territories_of_India" if local["kind"] != "country"
                else "https://en.wikipedia.org/wiki/List_of_sovereign_states",
                f"{nice} is {local['where']}. The claim says it is {'not ' if negated else ''}a {claimed}, so this source "
                f"{'supports' if stance == 'SUPPORTS' else 'contradicts'} it.",
                stance, 90.0))

    wiki = await _wikipedia_description(subject)
    if wiki and wiki["description"]:
        actual = _head_category(wiki["description"])
        stance = _verdict_for(claimed, actual, negated)
        if stance:
            items.append(_evidence(
                f"Wikipedia: {wiki['title']} — {wiki['description']}",
                "Wikipedia", wiki["url"] or f"https://en.wikipedia.org/wiki/{quote(wiki['title'].replace(' ', '_'))}",
                f"Wikipedia describes {wiki['title']} as \"{wiki['description']}\". "
                f"The claim says it is {'not ' if negated else ''}a {claimed}, so this {'supports' if stance == 'SUPPORTS' else 'contradicts'} it.",
                stance, 82.0))
    return items
