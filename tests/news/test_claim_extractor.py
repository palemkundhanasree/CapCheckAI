from app.engines.news.claim_extractor import extract_claims_from_text


def test_extract_claims_numeric_assertion():
    text = "The global average temperature reached a record high in 2023 according to climate scientists. The event caused widespread discussion."
    claims = extract_claims_from_text(text)
    assert len(claims) >= 1
    assert any("record high" in c["claim_text"].lower() or "2023" in c["claim_text"] for c in claims)


def test_extract_claims_empty_or_short():
    assert extract_claims_from_text("") == []
    short_claims = extract_claims_from_text("Hello there.")
    assert len(short_claims) == 1
