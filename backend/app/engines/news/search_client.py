import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus, urlparse
import httpx
from bs4 import BeautifulSoup
from app.engines.news.source_registry import lookup_source_reputation

logger = logging.getLogger(__name__)


async def search_duckduckgo_knowledge(query: str) -> List[Dict[str, Any]]:
    """
    Queries DuckDuckGo Instant Answer API for verified factual definitions and encyclopedia summaries.
    No API key required; highly reliable for general knowledge and verified records.
    """
    results = []
    url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            headers = {"User-Agent": "CapCheck-AI/1.0 (knowledge-retrieval)"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText", "").strip()
                heading = data.get("Heading", "").strip()
                source_url = data.get("AbstractURL", "")

                if abstract and len(abstract) > 20:
                    results.append({
                        "title": f"Background reference: {heading or query.title()}",
                        "source_name": data.get("AbstractSource", "Encyclopedia"),
                        "source_url": source_url or "https://duckduckgo.com",
                        "publisher": data.get("AbstractSource", "Authoritative Reference"),
                        "publish_date": "",
                        "snippet": abstract,
                        "stance": "NEUTRAL",
                        "credibility_score": 80.0,
                        "kind": "reference"
                    })
    except Exception as e:
        logger.debug(f"DuckDuckGo search error: {e}")

    return results


async def search_wikipedia_knowledge(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches Wikipedia API for factual grounding and historical context."""
    results = []
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "utf8": 1
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"User-Agent": "CapCheck-AI/1.0 (verification)"}
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    rep = lookup_source_reputation(page_url)
                    results.append({
                        "title": f"Background reference (Wikipedia): {title}",
                        "source_name": "Wikipedia",
                        "source_url": page_url,
                        "publisher": "Wikimedia Foundation",
                        "publish_date": "",
                        "snippet": snippet,
                        "stance": "NEUTRAL",
                        "credibility_score": rep["reliability"],
                        "kind": "reference"
                    })
    except Exception as e:
        logger.debug(f"Wikipedia search error: {e}")

    return results


async def search_web_evidence(query: str) -> List[Dict[str, Any]]:
    """Aggregates knowledge search across DuckDuckGo Instant Answers, Wikipedia, and open references."""
    evidence = []
    ddg_hits = await search_duckduckgo_knowledge(query)
    evidence.extend(ddg_hits)

    wiki_hits = await search_wikipedia_knowledge(query, limit=3)
    evidence.extend(wiki_hits)

    return evidence


# ---------------------------------------------------------------------------
# Live news coverage: find real articles, read them, and compare with the claim
# ---------------------------------------------------------------------------
from app.engines.news.claim_matcher import tokenize_clean  # noqa: E402
from app.engines.news.knowledge_checker import parse_is_a_claim, CATEGORY_VOCAB, _same_group  # noqa: E402

DEBUNK_CUES = re.compile(
    r"\b(fact[- ]check\w*|false|fake|hoax|debunk\w*|no evidence|misleading|baseless|unfounded|"
    r"fabricat\w*|not true|doctored|manipulated|misattributed|satire|rumou?r)\b",
    re.IGNORECASE,
)
NEWS_USER_AGENT = {"User-Agent": "Mozilla/5.0 (compatible; CapCheck-AI/1.0; +verification)"}


def key_terms(claim: str, limit: int = 7) -> List[str]:
    """Distinct content words of the claim, in order of appearance, used as a search query."""
    seen, terms = set(), []
    for w in re.findall(r"[A-Za-z0-9]{3,}", claim):
        lw = w.lower()
        if lw in seen or lw not in tokenize_clean(lw) and not lw.isdigit():
            continue
        seen.add(lw)
        terms.append(w)
        if len(terms) >= limit:
            break
    return terms


def analyze_text_against_claim(claim_tokens: set, title: str, text: str,
                               parsed: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Compares real page text with the claim. Returns None when the page does not discuss the claim.
    Otherwise returns the stance and the exact sentence that was matched so a person can check it.

    For "X is a Y" claims (parsed), a sentence only supports the claim if it also says Y; a sentence about X
    that names a different kind of thing (X is a *state*, claim says *country*) counts as contradicting it.
    """
    if not claim_tokens:
        return None
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", f"{title}. {text}") if len(x.strip()) > 25]
    subject_tokens = tokenize_clean(parsed["subject"]) if parsed else set()
    category = parsed["category"] if parsed else None
    negated = bool(parsed and parsed["negated"])

    best_sentence, best_overlap, debunk_hit, conflict_hit = "", 0.0, None, None
    for sent in sentences:
        low = sent.lower()
        toks = tokenize_clean(sent)
        overlap = len(claim_tokens & toks) / len(claim_tokens)

        if parsed and subject_tokens and subject_tokens <= toks:
            has_category = re.search(rf"\b{re.escape(category)}s?\b", low) is not None
            other = [w for w in CATEGORY_VOCAB if w != category and re.search(rf"\b{re.escape(w)}\b", low)
                     and _same_group(category, w) is False]
            if not has_category and other and conflict_hit is None and re.search(r"\b(is|are|was)\b", low):
                conflict_hit = (1.0, sent)
            if not has_category:
                continue  # talks about the subject but never says the claimed thing: not support
        if overlap > best_overlap:
            best_overlap, best_sentence = overlap, sent
        if overlap >= 0.34 and DEBUNK_CUES.search(sent) and (debunk_hit is None or overlap > debunk_hit[0]):
            debunk_hit = (overlap, sent)
    title_overlap = len(claim_tokens & tokenize_clean(title)) / len(claim_tokens)
    if debunk_hit is None and DEBUNK_CUES.search(title) and title_overlap >= 0.34:
        debunk_hit = (title_overlap, title)

    if conflict_hit:
        return {"stance": "SUPPORTS" if negated else "CONTRADICTS", "sentence": conflict_hit[1], "overlap": conflict_hit[0]}
    if debunk_hit:
        return {"stance": "CONTRADICTS", "sentence": debunk_hit[1], "overlap": debunk_hit[0]}
    if best_overlap >= 0.5:
        return {"stance": "CONTRADICTS" if negated else "SUPPORTS", "sentence": best_sentence, "overlap": best_overlap}
    return None


async def _read_article(url: str) -> Optional[Dict[str, Any]]:
    from app.engines.news.article_extractor import extract_article_content
    try:
        return await asyncio.wait_for(extract_article_content(url), timeout=9.0)
    except Exception as e:  # blocked, paywalled, timeout, unsafe URL
        logger.debug(f"Could not read {url}: {e}")
        return None


def _build_news_item(claim_tokens: set, url: str, title: str, domain: str, date: str,
                     text: str, read_page: bool, parsed: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    from app.engines.news.source_registry import lookup_source_reputation
    analysis = analyze_text_against_claim(claim_tokens, title, text, parsed)
    if not analysis:
        return None
    rep = lookup_source_reputation(url or domain)
    how = "Read the full article" if read_page else "Matched on the headline/summary only (page not readable)"
    verb = "reports a debunk or correction" if analysis["stance"] == "CONTRADICTS" else "reports the same claim"
    # A headline-only match is weaker evidence than a read article
    credibility = rep["reliability"] if read_page else min(rep["reliability"], 65.0)
    return {
        "title": title or "News article",
        "source_name": rep["name"] if rep.get("name") and rep["name"] != "Unknown Source" else (domain or "News source"),
        "source_url": url,
        "publisher": rep["name"],
        "publish_date": date,
        "snippet": f"{how}; this source {verb}. Matched passage: \"{analysis['sentence'][:280]}\"",
        "stance": analysis["stance"],
        "credibility_score": credibility,
        "kind": "news",
    }


async def search_news_coverage(claim: str, max_read: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Searches live news indexes (GDELT, Google News RSS), opens the returned articles,
    and checks what each one actually says about the claim.
    Returns (evidence_items, unavailable_notes). Nothing is invented: if the indexes
    cannot be reached the list is empty and the note says so.
    """
    terms = key_terms(claim)
    if len(terms) < 2:
        return [], []
    query = " ".join(terms)
    claim_tokens = tokenize_clean(claim)
    parsed = parse_is_a_claim(claim)
    notes: List[str] = []
    items: List[Dict[str, Any]] = []
    candidates: List[Dict[str, str]] = []

    async with httpx.AsyncClient(timeout=8.0, headers=NEWS_USER_AGENT, follow_redirects=True) as client:
        # 1) GDELT article index (direct publisher URLs)
        gdelt_ok = False
        try:
            r = await client.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={"query": query, "mode": "artlist", "maxrecords": 10, "format": "json", "sort": "hybridrel"},
            )
            if r.status_code == 200 and r.text.strip().startswith("{"):
                gdelt_ok = True
                for a in r.json().get("articles", []):
                    if a.get("url") and (a.get("language", "English") in ("English", "")):
                        candidates.append({"url": a["url"], "title": a.get("title", ""),
                                           "domain": a.get("domain", ""), "date": (a.get("seendate") or "")[:8]})
        except Exception as e:
            logger.debug(f"GDELT error: {e}")
        if not gdelt_ok:
            notes.append("GDELT global news index could not be reached")

        # 2) Google News RSS (headline + publisher; used when pages cannot be opened)
        rss_items: List[Dict[str, str]] = []
        try:
            r = await client.get("https://news.google.com/rss/search",
                                 params={"q": query, "hl": "en", "gl": "US", "ceid": "US:en"})
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for it in root.iter("item"):
                    src = it.find("source")
                    rss_items.append({
                        "title": (it.findtext("title") or "").strip(),
                        "link": (it.findtext("link") or "").strip(),
                        "date": (it.findtext("pubDate") or "")[:16],
                        "source": (src.text or "").strip() if src is not None else "",
                        "source_url": src.get("url", "") if src is not None else "",
                        "desc": BeautifulSoup(it.findtext("description") or "", "html.parser").get_text(" ").strip(),
                    })
                    if len(rss_items) >= 10:
                        break
            else:
                notes.append("Google News search could not be reached")
        except Exception as e:
            logger.debug(f"Google News RSS error: {e}")
            notes.append("Google News search could not be reached")

    # Read the top GDELT articles in parallel
    seen_domains = set()
    to_read = []
    for c in candidates:
        dom = urlparse(c["url"]).netloc.lower().removeprefix("www.")
        if dom in seen_domains:
            continue
        seen_domains.add(dom)
        to_read.append(c)
        if len(to_read) >= max_read:
            break
    pages = await asyncio.gather(*[_read_article(c["url"]) for c in to_read]) if to_read else []
    for c, page in zip(to_read, pages):
        if page and page.get("body_text"):
            item = _build_news_item(claim_tokens, page.get("canonical_url") or c["url"],
                                    page.get("title") or c["title"], c["domain"],
                                    page.get("publication_date") or c["date"], page["body_text"], True, parsed)
            if item:
                items.append(item)

    # Add headline-level matches from RSS for publishers not already read
    for it in rss_items:
        dom = urlparse(it["source_url"]).netloc.lower().removeprefix("www.") if it["source_url"] else ""
        if dom and dom in seen_domains:
            continue
        item = _build_news_item(claim_tokens, it["source_url"] or it["link"], it["title"],
                                dom or it["source"], it["date"], it["desc"], False, parsed)
        if item:
            item["source_name"] = it["source"] or item["source_name"]
            item["source_url"] = it["link"] or it["source_url"]
            items.append(item)
            if dom:
                seen_domains.add(dom)

    return items[:8], notes
