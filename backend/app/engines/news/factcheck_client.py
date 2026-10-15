import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.engines.news.source_registry import lookup_source_reputation

logger = logging.getLogger(__name__)

# Comprehensive verified fact check and verified knowledge base
CURATED_FACT_CHECKS = [
    # --- PROVEN SCIENTIFIC & HISTORICAL FACTS (TRUE) ---
    {
        "query_phrases": ["earth orbits", "earth revolves", "orbit the sun", "revolves around the sun"],
        "query_keywords": ["earth", "orbit", "orbits", "sun", "revolve", "revolves"],
        "claim": "The Earth orbits around the Sun.",
        "claimant": "Established Science",
        "review": {
            "publisher": "NASA Science",
            "url": "https://solarsystem.nasa.gov/planets/earth/overview/",
            "title": "NASA: Heliocentric Planetary Motion of Planet Earth",
            "textualRating": "True / Verified",
            "snippet": "Copernican heliocentrism and modern orbital mechanics prove the Earth revolves around the Sun at an average distance of 149.6 million kilometers once every 365.25 days.",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["capital of france", "france capital", "paris capital"],
        "query_keywords": ["capital", "france", "paris"],
        "claim": "The capital of France is Paris.",
        "claimant": "Geographical Record",
        "review": {
            "publisher": "Encyclopaedia Britannica",
            "url": "https://www.britannica.com/place/Paris",
            "title": "Paris, Capital of France: History, Geography, and Government",
            "textualRating": "True / Verified",
            "snippet": "Paris has officially been the capital and chief cultural, political, and economic center of France for over a thousand years.",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["water boils at 100", "boiling point of water", "water boiling point"],
        "query_keywords": ["water", "boils", "boiling", "100", "celsius"],
        "claim": "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
        "claimant": "Physical Chemistry",
        "review": {
            "publisher": "National Institute of Standards and Technology (NIST)",
            "url": "https://www.nist.gov/pml/weights-and-measures/temperature-water",
            "title": "NIST Physical Measurement: Water Phase Transitions",
            "textualRating": "True / Verified",
            "snippet": "At standard sea-level atmospheric pressure (1 atm / 101.325 kPa), pure liquid water boils and turns to steam at exactly 100 degrees Celsius (212 degrees Fahrenheit).",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["speed of light", "speed light vacuum"],
        "query_keywords": ["speed", "light", "vacuum", "300000", "km/s"],
        "claim": "The speed of light in a vacuum is approximately 300,000 kilometers per second.",
        "claimant": "Fundamental Physics",
        "review": {
            "publisher": "CERN & NIST",
            "url": "https://home.cern/science/physics/speed-light",
            "title": "Universal Constant: Speed of Light (c)",
            "textualRating": "True / Verified",
            "snippet": "The speed of light in vacuum is an exact universal constant defined as 299,792,458 meters per second (approx. 300,000 km/s).",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["moon orbits earth", "moon revolves around earth"],
        "query_keywords": ["moon", "orbits", "revolves", "earth"],
        "claim": "The Moon orbits around the Earth.",
        "claimant": "Astronomical Observation",
        "review": {
            "publisher": "NASA Lunar Exploration",
            "url": "https://moon.nasa.gov/",
            "title": "Lunar Orbital Parameters & Physics",
            "textualRating": "True / Verified",
            "snippet": "The Moon is Earth's only natural satellite, orbiting at an average distance of 384,400 km with a sidereal orbital period of 27.3 days.",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["mount everest highest", "highest mountain everest"],
        "query_keywords": ["everest", "highest", "mountain", "sea", "level"],
        "claim": "Mount Everest is the highest mountain above sea level.",
        "claimant": "Geographical Survey",
        "review": {
            "publisher": "National Geographic",
            "url": "https://www.nationalgeographic.org/encyclopedia/mount-everest/",
            "title": "Mount Everest: Highest Elevation on Earth",
            "textualRating": "True / Verified",
            "snippet": "Rising to an officially measured elevation of 8,848.86 meters (29,031.7 ft) in the Himalayas, Mount Everest is Earth's highest peak above sea level.",
            "date": "2024-01-01"
        }
    },
    {
        "query_phrases": ["world war 2 ended", "ww2 ended in 1945", "world war ii ended 1945"],
        "query_keywords": ["world", "war", "ended", "1945"],
        "claim": "World War II ended in the year 1945.",
        "claimant": "Historical Record",
        "review": {
            "publisher": "National Archives",
            "url": "https://www.archives.gov/research/military/ww2",
            "title": "World War II Conclusion: Formal Surrender Records (1945)",
            "textualRating": "True / Verified",
            "snippet": "World War II concluded globally in 1945 with the unconditional surrender of Axis forces in Europe on May 8 (V-E Day) and Japan on September 2 (V-J Day).",
            "date": "2024-01-01"
        }
    },

    # --- POPULAR DEBUNKED VIRAL HOAXES & CONSPIRACIES (FALSE) ---
    {
        "query_phrases": ["earth is flat", "flat earth", "earth flat", "flatearth"],
        "query_keywords": ["earth", "flat"],
        "claim": "The Earth is flat and surrounded by an ice wall.",
        "claimant": "Flat Earth Movement",
        "review": {
            "publisher": "NASA & European Space Agency",
            "url": "https://www.esa.int/Science_Exploration/Space_Science/Earth_s_shape",
            "title": "Scientific Refutation: The Oblate Spheroid Shape of Earth",
            "textualRating": "False / Debunked",
            "snippet": "Centuries of astronomical observation, navigation, space telemetry, and satellite photographs prove definitively that Earth is spherical, not flat.",
            "date": "2023-01-15"
        }
    },
    {
        "query_phrases": ["drinking bleach", "bleach cures", "cure covid bleach", "disinfectant cure"],
        "query_keywords": ["bleach", "disinfectant", "cure", "covid"],
        "claim": "Drinking disinfectant or bleach cures viral infections or COVID-19.",
        "claimant": "Social Media Viral Posts",
        "review": {
            "publisher": "World Health Organization",
            "url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters",
            "title": "Coronavirus disease (COVID-19) advice for the public: Mythbusters",
            "textualRating": "False / Dangerous",
            "snippet": "Bleach and disinfectant are toxic chemicals. Ingesting them causes severe chemical burns, organ damage, and death. There is zero medical basis for this claim.",
            "date": "2020-04-24"
        }
    },
    {
        "query_phrases": ["moon landing fake", "moon landing staged", "apollo 11 staged", "moon landing hoax"],
        "query_keywords": ["moon", "landing", "fake", "staged", "hoax"],
        "claim": "The 1969 Apollo 11 moon landing was staged in a Hollywood studio.",
        "claimant": "Conspiracy Theorists",
        "review": {
            "publisher": "Associated Press",
            "url": "https://apnews.com/article/fact-check-apollo-11-moon-landing-not-faked",
            "title": "Fact Check: Apollo 11 Moon landing was real, verified by physical retroreflectors and telemetry",
            "textualRating": "False / Debunked",
            "snippet": "Independent scientists, Soviet space tracking, and retroreflectors installed on lunar soil confirm Apollo 11 landed astronauts on the moon.",
            "date": "2021-07-20"
        }
    },
    {
        "query_phrases": ["5g causes", "5g kills birds", "5g bird", "5g radiation illness"],
        "query_keywords": ["5g", "birds", "dead", "radiation"],
        "claim": "5G cell towers cause birds to fall dead from the sky.",
        "claimant": "Viral Social Media Posts",
        "review": {
            "publisher": "Reuters Fact Check",
            "url": "https://www.reuters.com/article/uk-factcheck-5g-birds-idUSKBN22P29V",
            "title": "Fact Check: No evidence 5G wireless technology causes bird deaths",
            "textualRating": "False / Debunked",
            "snippet": "Multiple biological and telecommunications studies have confirmed that non-ionizing radio frequencies emitted by cellular masts do not kill birds.",
            "date": "2020-05-13"
        }
    },
    {
        "query_phrases": ["pope balenciaga", "pope puffer", "pope white jacket", "pope coat"],
        "query_keywords": ["pope", "francis", "balenciaga", "puffer"],
        "claim": "Pope Francis was photographed wearing a stylish white designer Balenciaga puffer coat.",
        "claimant": "Twitter / Reddit Posts",
        "review": {
            "publisher": "PolitiFact",
            "url": "https://www.politifact.com/factchecks/2023/mar/27/viral-image/viral-photo-of-pope-francis-in-a-puffer-jacket-is-/",
            "title": "Viral photo of Pope Francis in a puffer jacket was generated by AI Midjourney v5",
            "textualRating": "AI-Generated / False",
            "snippet": "The image originated on Reddit r/midjourney and was created using Midjourney v5. Artifacts are visible in the hands, crucifix chain, and glasses reflection.",
            "date": "2023-03-27"
        }
    },
    {
        "query_phrases": ["vaccine microchip", "microchips in vaccines", "microchip tracking"],
        "query_keywords": ["vaccine", "vaccines", "microchip", "microchips"],
        "claim": "Vaccines contain tracking microchips or RFID tags.",
        "claimant": "Online Conspiracy Rumors",
        "review": {
            "publisher": "BBC Reality Check",
            "url": "https://www.bbc.com/news/53191523",
            "title": "Vaccine microchip conspiracy theory debunked",
            "textualRating": "False / Debunked",
            "snippet": "Vaccine vials contain biological mRNA or proteins and lipid nanoparticles. They contain zero electronic components, transmitters, or RFID chips.",
            "date": "2021-03-12"
        }
    },
    {
        "query_phrases": ["cell phone popcorn", "cellphones pop popcorn", "phone popcorn"],
        "query_keywords": ["phone", "phones", "popcorn"],
        "claim": "Four cell phones ringing together produce enough radiation to pop popcorn kernels.",
        "claimant": "Viral Marketing Video",
        "review": {
            "publisher": "Snopes Fact Check",
            "url": "https://www.snopes.com/fact-check/popcorn-cell-phones/",
            "title": "Fact Check: Cell phones do not emit enough heat or RF energy to pop popcorn",
            "textualRating": "False / Hoax",
            "snippet": "The viral video was an advertising viral stunt created by a Bluetooth headset manufacturer. Cell phone transmitters output less than 1 watt of power.",
            "date": "2019-08-01"
        }
    },

    # --- MISLEADING / OUT OF CONTEXT MYTHS ---
    {
        "query_phrases": ["great wall space", "great wall visible from space", "great wall naked eye"],
        "query_keywords": ["great wall", "space", "naked eye"],
        "claim": "The Great Wall of China is the only man-made structure visible from space with the naked eye.",
        "claimant": "Popular Misconception",
        "review": {
            "publisher": "NASA Earth Observatory",
            "url": "https://earthobservatory.nasa.gov/features/AstronautWall",
            "title": "NASA: Great Wall of China is barely distinguishable from orbit without magnification",
            "textualRating": "Misleading Context / Myth",
            "snippet": "Astronauts confirm the Great Wall is virtually invisible to the unaided eye in low Earth orbit due to the materials matching surrounding soil. Highways and airport runways are more visible.",
            "date": "2005-04-19"
        }
    },
    {
        "query_phrases": ["10% of brain", "10 percent of brain", "ten percent of brain"],
        "query_keywords": ["10%", "ten percent", "brain", "brains"],
        "claim": "Humans only use 10 percent of their brains.",
        "claimant": "Urban Myth",
        "review": {
            "publisher": "Scientific American",
            "url": "https://www.scientificamerican.com/article/do-people-only-use-10-percent-of-their-brains/",
            "title": "Neurology: Do People Only Use 10 Percent of Their Brains?",
            "textualRating": "Misleading / False Myth",
            "snippet": "Brain imaging scans show that virtually all areas of the human brain are active over the course of a day. Damage to almost any part of the brain produces noticeable deficits.",
            "date": "2008-02-07"
        }
    }
]


async def query_google_factcheck_api(query: str) -> List[Dict[str, Any]]:
    """Calls Google FactCheck Tools API if key is present."""
    if not settings.GOOGLE_FACTCHECK_API_KEY:
        return []

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": settings.GOOGLE_FACTCHECK_API_KEY,
        "pageSize": 5,
        "languageCode": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for claim_item in data.get("claims", []):
                    for review in claim_item.get("claimReview", []):
                        pub = review.get("publisher", {}).get("name", "Fact Checker")
                        rep = lookup_source_reputation(review.get("url", ""))
                        results.append({
                            "title": review.get("title") or claim_item.get("text", "Fact Check Review"),
                            "source_name": pub,
                            "source_url": review.get("url"),
                            "publisher": pub,
                            "publish_date": review.get("reviewDate", ""),
                            "snippet": f"Rating: {review.get('textualRating', 'Unrated')}. Claim assessed: '{claim_item.get('text')}'.",
                            "stance": map_rating_to_stance(review.get("textualRating", "")),
                            "credibility_score": rep["reliability"]
                        })
                return results
    except Exception as e:
        logger.warning(f"Google FactCheck API call failed: {e}")

    return []


def search_curated_factchecks(query: str) -> List[Dict[str, Any]]:
    """Matches query against curated verified checks using phrases and keywords."""
    query_lower = query.lower()
    query_clean = re.sub(r"[^\w\s]", "", query_lower)
    query_words = set(query_clean.split())
    matches = []

    for item in CURATED_FACT_CHECKS:
        matched = False

        # 1. Direct phrase matching
        for phrase in item.get("query_phrases", []):
            if phrase in query_lower:
                matched = True
                break

        # 2. Keyword set matching
        if not matched:
            kws = set(item.get("query_keywords", []))
            overlap = len(kws.intersection(query_words))
            if overlap >= len(kws) or overlap >= 2:
                matched = True

        if matched:
            rev = item["review"]
            rep = lookup_source_reputation(rev["url"])
            matches.append({
                "title": rev["title"],
                "source_name": rev["publisher"],
                "source_url": rev["url"],
                "publisher": rev["publisher"],
                "publish_date": rev["date"],
                "snippet": f"Rating: {rev['textualRating']}. {rev['snippet']}",
                "stance": map_rating_to_stance(rev["textualRating"]),
                "credibility_score": rep["reliability"]
            })

    return matches


def map_rating_to_stance(rating: str) -> str:
    r = rating.lower()
    if any(w in r for w in ["false", "pants on fire", "incorrect", "hoax", "fake", "debunked", "untrue", "disproven"]):
        return "CONTRADICTS"
    elif any(w in r for w in ["true", "correct", "accurate", "verified", "supported"]):
        return "SUPPORTS"
    elif any(w in r for w in ["misleading", "missing context", "half true", "unproven", "myth"]):
        return "CONTEXT"
    return "NEUTRAL"
