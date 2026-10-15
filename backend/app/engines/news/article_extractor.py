import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from app.security.url_safety import safe_fetch_url


async def extract_article_content(url: str) -> Dict[str, Any]:
    """
    Safely retrieves public web page, strips scripts/ads/nav,
    and extracts structured article metadata and body text.
    """
    html_text, final_url, status_code = await safe_fetch_url(url)
    soup = BeautifulSoup(html_text, "html.parser")

    # Clean unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript", "svg", "button", "iframe"]):
        tag.decompose()

    # Extract Title
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()

    # Extract Publisher / Site Name
    publisher = ""
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        publisher = og_site["content"].strip()

    # Extract Publication Date
    pub_date = ""
    date_tags = [
        soup.find("meta", property="article:published_time"),
        soup.find("meta", attrs={"name": "publication_date"}),
        soup.find("meta", attrs={"name": "date"}),
        soup.find("time")
    ]
    for dt in date_tags:
        if dt:
            pub_date = dt.get("content") or dt.get("datetime") or dt.get_text()
            if pub_date:
                pub_date = pub_date.strip()
                break

    # Extract Author
    author = ""
    author_tag = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
    if author_tag and author_tag.get("content"):
        author = author_tag["content"].strip()

    # Extract Main Body Text
    article_tag = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|post|story|article", re.I))
    paragraphs = []
    if article_tag:
        for p in article_tag.find_all("p"):
            text = p.get_text().strip()
            if len(text) > 30:  # Skip tiny fragments
                paragraphs.append(text)
    else:
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if len(text) > 30:
                paragraphs.append(text)

    full_body = "\n\n".join(paragraphs[:30])  # Cap at 30 paragraphs for safety

    return {
        "title": title or "Untitled Article",
        "publisher": publisher,
        "author": author,
        "publication_date": pub_date,
        "canonical_url": final_url,
        "body_text": full_body,
        "word_count": len(full_body.split()),
    }
