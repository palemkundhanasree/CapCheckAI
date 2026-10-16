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
    "britannica.com": {"name": "Encyclopaedia Britannica", "category": "ENCYCLOPEDIA", "reliability": 96.0, "ifcn": False},
    "nationalgeographic.com": {"name": "National Geographic", "category": "ACADEMIC", "reliability": 94.0, "ifcn": False},
    "nationalgeographic.org": {"name": "National Geographic", "category": "ACADEMIC", "reliability": 94.0, "ifcn": False},
    "scientificamerican.com": {"name": "Scientific American", "category": "ACADEMIC", "reliability": 94.0, "ifcn": False},
    "wikipedia.org": {"name": "Wikipedia", "category": "ENCYCLOPEDIA", "reliability": 88.0, "ifcn": False},
    "who.int": {"name": "World Health Organization", "category": "INSTITUTION", "reliability": 95.0, "ifcn": False},
    "cdc.gov": {"name": "Centers for Disease Control", "category": "INSTITUTION", "reliability": 95.0, "ifcn": False},
    "nasa.gov": {"name": "NASA", "category": "INSTITUTION", "reliability": 98.0, "ifcn": False},
    "nist.gov": {"name": "National Institute of Standards and Technology", "category": "INSTITUTION", "reliability": 98.0, "ifcn": False},
    "cern.ch": {"name": "CERN", "category": "ACADEMIC", "reliability": 98.0, "ifcn": False},
    "home.cern": {"name": "CERN", "category": "ACADEMIC", "reliability": 98.0, "ifcn": False},
    "esa.int": {"name": "European Space Agency", "category": "INSTITUTION", "reliability": 96.0, "ifcn": False},
    "archives.gov": {"name": "National Archives", "category": "INSTITUTION", "reliability": 96.0, "ifcn": False},
    "un.org": {"name": "United Nations", "category": "INSTITUTION", "reliability": 94.0, "ifcn": False},
    "nih.gov": {"name": "National Institutes of Health", "category": "INSTITUTION", "reliability": 96.0, "ifcn": False},
}


def lookup_source_reputation(url_or_domain: str) -> dict:
    """Extracts domain and looks up credibility score and category."""
    if not url_or_domain:
        return {"name": "Unknown Source", "category": "GENERAL", "reliability": 30.0, "ifcn": False}

    domain = url_or_domain.lower()
    if "://" in domain:
        domain = urlparse(domain).netloc

    domain = domain.split(":")[0]  # Strip port
    if domain.startswith("www."):
        domain = domain[4:]

    # Check for IP addresses or localhost
    is_ip = False
    try:
        import ipaddress
        ipaddress.ip_address(domain)
        is_ip = True
    except ValueError:
        is_ip = False

    if is_ip or domain in ("localhost", "127.0.0.1", "0.0.0.0"):
        return {
            "name": f"Restricted Host ({domain})",
            "category": "RESTRICTED_OR_PRIVATE",
            "reliability": 0.0,
            "ifcn": False,
            "domain": domain
        }

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
    if domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".int"):
        return {"name": domain.title(), "category": "INSTITUTION", "reliability": 92.0, "ifcn": False, "domain": domain}

    if domain.endswith(".org"):
        return {"name": domain.title(), "category": "ORGANIZATION", "reliability": 80.0, "ifcn": False, "domain": domain}

    # Generic unverified commercial or blog web domains
    return {"name": domain.title(), "category": "UNVERIFIED_WEB", "reliability": 50.0, "ifcn": False, "domain": domain}
