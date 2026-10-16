import logging
import re
from typing import List, Dict, Any
from urllib.parse import quote_plus
import httpx
from app.config import settings
from app.engines.news.source_registry import lookup_source_reputation

logger = logging.getLogger(__name__)


def extract_search_keywords(query: str, max_words: int = 6) -> str:
    """Extracts high-signal keywords from complex claim sentences for web search."""
    clean = re.sub(r"[^\w\s]", " ", query)
    words = clean.split()
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "been", "being",
        "and", "or", "but", "in", "on", "at", "to", "for", "with", "by",
        "about", "against", "between", "into", "through", "during", "before",
        "after", "above", "below", "from", "up", "down", "of", "off", "over",
        "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "any", "both", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "can", "will", "just", "should",
        "now", "that", "this", "these", "those"
    }
    keywords = [w for w in words if w.lower() not in stopwords and len(w) > 2]
    if not keywords:
        keywords = words[:max_words]
    return " ".join(keywords[:max_words])


async def search_bing_news(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Queries Microsoft Bing News Search v7 API if configured."""
    if not getattr(settings, "BING_SEARCH_API_KEY", ""):
        return []

    results = []
    url = "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": settings.BING_SEARCH_API_KEY}
    params = {"q": query, "count": limit, "mkt": "en-US", "freshness": "Month"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for article in data.get("value", []):
                    title = article.get("name", "")
                    news_url = article.get("url", "")
                    snippet = article.get("description", "")
                    provider = article.get("provider", [{}])[0].get("name", "News Provider")
                    pub_date = article.get("datePublished", "")

                    rep = lookup_source_reputation(news_url)
                    results.append({
                        "title": title,
                        "source_name": provider or rep.get("name", "News Outlet"),
                        "source_url": news_url,
                        "publisher": provider,
                        "publish_date": pub_date[:10] if pub_date else "Recent News",
                        "snippet": snippet,
                        "stance": "NEUTRAL",
                        "credibility_score": rep.get("reliability", 85.0)
                    })
    except Exception as e:
        logger.warning(f"Bing News Search API error: {e}")

    return results


async def search_newsapi(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Queries NewsAPI.org for global news coverage if configured."""
    if not getattr(settings, "NEWS_API_KEY", ""):
        return []

    results = []
    kw_query = extract_search_keywords(query, max_words=5)
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": kw_query or query[:50],
        "apiKey": settings.NEWS_API_KEY,
        "pageSize": limit,
        "language": "en",
        "sortBy": "relevancy"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for article in data.get("articles", []):
                    title = article.get("title", "")
                    article_url = article.get("url", "")
                    source_name = article.get("source", {}).get("name", "News")
                    snippet = article.get("description") or article.get("content", "")

                    rep = lookup_source_reputation(article_url)
                    results.append({
                        "title": title,
                        "source_name": source_name,
                        "source_url": article_url,
                        "publisher": source_name,
                        "publish_date": (article.get("publishedAt") or "")[:10] or "Recent",
                        "snippet": snippet[:200] if snippet else "",
                        "stance": "NEUTRAL",
                        "credibility_score": rep.get("reliability", 85.0)
                    })
    except Exception as e:
        logger.warning(f"NewsAPI query error: {e}")

    return results


async def search_duckduckgo_knowledge(query: str) -> List[Dict[str, Any]]:
    """
    Queries DuckDuckGo Instant Answer API for verified definitions and encyclopedic summaries.
    No API key required; highly reliable for general knowledge and verified records.
    """
    results = []
    # Try with focused keywords first if query is long
    search_q = extract_search_keywords(query, max_words=5) if len(query.split()) > 6 else query
    url = f"https://api.duckduckgo.com/?q={quote_plus(search_q)}&format=json&no_html=1&skip_disambig=1"

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
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

                # Related topics
                for topic in data.get("RelatedTopics", [])[:3]:
                    text = topic.get("Text", "")
                    first_url = topic.get("FirstURL", "")
                    if text and first_url:
                        rep = lookup_source_reputation(first_url)
                        results.append({
                            "title": f"Internet Reference: {text[:60]}...",
                            "source_name": rep.get("name", "Web Reference"),
                            "source_url": first_url,
                            "publisher": rep.get("name", "Public Source"),
                            "publish_date": "Public Index",
                            "snippet": text,
                            "stance": "NEUTRAL",
                            "credibility_score": rep.get("reliability", 85.0)
                        })
    except Exception as e:
        logger.debug(f"DuckDuckGo search error: {e}")

    return results


async def search_wikipedia_knowledge(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches Wikipedia API for factual grounding and historical context."""
    results = []
    # If query is long sentence, distill to search keywords
    search_term = extract_search_keywords(query, max_words=5) if len(query.split()) > 5 else query

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": search_term,
        "format": "json",
        "srlimit": limit,
        "utf8": 1
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
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
                        "credibility_score": rep.get("reliability", 88.0)
                    })
    except Exception as e:
        logger.debug(f"Wikipedia search error: {e}")

    return results


async def search_web_evidence(query: str) -> List[Dict[str, Any]]:
    """
    Aggregates knowledge search across Bing News, NewsAPI, DuckDuckGo Instant Answers,
    and Wikipedia with graceful fallback and deduplication.
    """
    evidence = []

    # 1. Live News APIs (if configured)
    bing_hits = await search_bing_news(query)
    evidence.extend(bing_hits)

    newsapi_hits = await search_newsapi(query)
    evidence.extend(newsapi_hits)

    # 2. Knowledge & Encyclopedia Engines
    wiki_hits = await search_wikipedia_knowledge(query, limit=3)
    evidence.extend(wiki_hits)

    ddg_hits = await search_duckduckgo_knowledge(query)
    evidence.extend(ddg_hits)

    # Deduplicate results by URL
    seen_urls = set()
    deduped = []
    for item in evidence:
        u = item.get("source_url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            deduped.append(item)

    return deduped
