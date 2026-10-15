import logging
from typing import List, Dict, Any
from urllib.parse import quote_plus
import httpx
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
                        "title": f"Verified Reference: {heading or query.title()}",
                        "source_name": data.get("AbstractSource", "Encyclopedia"),
                        "source_url": source_url or "https://duckduckgo.com",
                        "publisher": data.get("AbstractSource", "Authoritative Reference"),
                        "publish_date": "Verified Knowledge Base",
                        "snippet": abstract,
                        "stance": "NEUTRAL",
                        "credibility_score": 92.0
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
            headers = {"User-Agent": "CapCheck-AI/1.0 (academic/verification; contact@capcheck.local)"}
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    rep = lookup_source_reputation(page_url)
                    results.append({
                        "title": f"Wikipedia: {title}",
                        "source_name": "Wikipedia",
                        "source_url": page_url,
                        "publisher": "Wikimedia Foundation",
                        "publish_date": "Updated recently",
                        "snippet": snippet,
                        "stance": "NEUTRAL",
                        "credibility_score": rep["reliability"]
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
