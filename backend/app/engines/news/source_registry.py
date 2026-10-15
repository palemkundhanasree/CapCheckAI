from typing import Dict, Optional
from urllib.parse import urlparse

KNOWN_SOURCES: Dict[str, dict] = {
    "reuters.com": {"name": "Reuters", "category": "NEWS_WIRE", "reliability": 95.0, "ifcn": False},
    "apnews.com": {"name": "Associated Press", "category": "NEWS_WIRE", "reliability": 95.0, "ifcn": True},
    "politifact.com": {"name": "PolitiFact", "category": "FACT_CHECKER", "reliability": 92.0, "ifcn": True},
    "snopes.com": {"name": "Snopes", "category": "FACT_CHECKER", "reliability": 90.0, "ifcn": True},
    "factcheck.org": {"name": "FactCheck.org", "category": "FACT_CHECKER", "reliability": 93.0, "ifcn": True},
    "bbc.com": {"name": "BBC News / Reality Check", "category": "MAINSTREAM_MEDIA", "reliability": 90.0, "ifcn": False},
    "afp.com": {"name": "Agence France-Presse (AFP)", "category": "FACT_CHECKER", "reliability": 92.0, "ifcn": True},
    "fullfact.org": {"name": "Full Fact", "category": "FACT_CHECKER", "reliability": 91.0, "ifcn": True},
    "washingtonpost.com": {"name": "The Washington Post Fact Checker", "category": "MAINSTREAM_MEDIA", "reliability": 88.0, "ifcn": True},
    "nytimes.com": {"name": "The New York Times", "category": "MAINSTREAM_MEDIA", "reliability": 88.0, "ifcn": False},
    "nature.com": {"name": "Nature Journal", "category": "ACADEMIC", "reliability": 98.0, "ifcn": False},
    "science.org": {"name": "Science", "category": "ACADEMIC", "reliability": 98.0, "ifcn": False},
    "wikipedia.org": {"name": "Wikipedia", "category": "ENCYCLOPEDIA", "reliability": 80.0, "ifcn": False},
    "who.int": {"name": "World Health Organization", "category": "INSTITUTION", "reliability": 94.0, "ifcn": False},
    "cdc.gov": {"name": "Centers for Disease Control", "category": "INSTITUTION", "reliability": 94.0, "ifcn": False},
    "nasa.gov": {"name": "NASA", "category": "INSTITUTION", "reliability": 96.0, "ifcn": False},
}


def lookup_source_reputation(url_or_domain: str) -> dict:
    """Extracts domain and looks up credibility score and category."""
    if not url_or_domain:
        return {"name": "Unknown Source", "category": "GENERAL", "reliability": 50.0, "ifcn": False}

    domain = url_or_domain.lower()
    if "://" in domain:
        domain = urlparse(domain).netloc

    domain = domain.split(":")[0]  # Strip port
    if domain.startswith("www."):
        domain = domain[4:]

    # Direct match
    if domain in KNOWN_SOURCES:
        info = KNOWN_SOURCES[domain]
        return {
            "name": info["name"],
            "category": info["category"],
            "reliability": info["reliability"],
            "ifcn": info["ifcn"],
            "domain": domain
        }

    # Suffix match (e.g. en.wikipedia.org matches wikipedia.org)
    for known_dom, info in KNOWN_SOURCES.items():
        if domain.endswith("." + known_dom):
            return {
                "name": info["name"],
                "category": info["category"],
                "reliability": info["reliability"],
                "ifcn": info["ifcn"],
                "domain": known_dom
            }

    # Fallback default score based on TLD
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return {"name": domain.title(), "category": "INSTITUTION", "reliability": 85.0, "ifcn": False, "domain": domain}

    return {"name": domain.title(), "category": "WEB_SOURCE", "reliability": 60.0, "ifcn": False, "domain": domain}
