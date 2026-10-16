import asyncio
from app.engines.news.knowledge_checker import parse_is_a_claim, check_entity_type_claim


def stances(claim):
    return [e["stance"] for e in asyncio.run(check_entity_type_claim(claim)) if e["source_name"].startswith("Built-in")]


def test_state_is_not_a_country():
    assert parse_is_a_claim("Andhra Pradesh is a country")["category"] == "country"
    assert stances("Andhra Pradesh is a country") == ["CONTRADICTS"]
    assert stances("andhara Pradesh is country") == ["CONTRADICTS"]  # spelling slip, no article


def test_state_is_a_state():
    assert stances("Andhra Pradesh is a state") == ["SUPPORTS"]
    assert stances("Andhra Pradesh is not a country") == ["SUPPORTS"]


def test_country_claims():
    assert stances("France is a country") == ["SUPPORTS"]
    assert stances("Telangana is a city") == ["CONTRADICTS"]
