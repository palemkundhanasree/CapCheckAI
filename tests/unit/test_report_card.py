"""Report card: per-test breakdown, grade and the honest 'no percentage' case."""
from app.services.verdict_engine import VerdictEngine


def ev(stance, kind, cred, pub):
    return {"stance": stance, "kind": kind, "credibility_score": cred, "publisher": pub, "source_name": pub, "title": "t"}


def card_for_claim(items):
    verdict = VerdictEngine.evaluate_claim_verdict(items)
    return VerdictEngine.synthesize_overall_verdict("claim", verdict, None, None, items, [], [])


def test_debunked_claim_gets_failing_grade_and_per_group_breakdown():
    items = [ev("CONTRADICTS", "factcheck", 90, "Snopes"), ev("CONTRADICTS", "knowledge", 92, "Reference"),
             ev("CONTRADICTS", "news", 95, "Reuters")]
    syn = card_for_claim(items)
    assert syn.correctness_score <= 10
    card = syn.report_card
    assert card["grade"] == "F"
    assert {s["key"] for s in card["sections"]} >= {"factcheck", "knowledge", "news"}
    assert all(s["status"] == "bad" for s in card["sections"])


def test_no_evidence_gives_no_percentage_instead_of_a_guess():
    syn = card_for_claim([])
    assert syn.correctness_score is None
    assert syn.report_card["grade"] == "?"
    assert syn.report_card["overall_percent"] is None


def test_group_without_a_position_is_reported_as_no_result_not_zero():
    syn = card_for_claim([ev("SUPPORTS", "news", 85, "BBC")])
    fact = [s for s in syn.report_card["sections"] if s["key"] == "factcheck"][0]
    assert fact["percent"] is None and fact["status"] == "unknown"


def test_media_card_uses_detector_details_and_caps_at_88():
    details = [
        {"key": "ai", "title": "AI-generation tests", "risk": 5, "detail": ""},
        {"key": "m", "title": "Editing test", "risk": 8, "detail": ""},
        {"key": "p", "title": "Provenance", "risk": None, "detail": "none"},
    ]
    verdict = VerdictEngine.evaluate_media_authenticity(5, 8, [])
    syn = VerdictEngine.synthesize_overall_verdict("image", None, verdict, None, [], [5, 8], [], detector_details=details)
    secs = {s["key"]: s for s in syn.report_card["sections"]}
    assert secs["ai"]["percent"] == 88.0          # never 95%: tests cannot prove authenticity
    assert secs["p"]["percent"] is None           # a test that could not judge is not scored
    assert syn.correctness_score <= 88


def test_ai_metadata_image_is_graded_failing():
    details = [{"key": "ai", "title": "AI-generation tests", "risk": 96, "detail": ""}]
    verdict = VerdictEngine.evaluate_media_authenticity(96, 8, [])
    syn = VerdictEngine.synthesize_overall_verdict("image", None, verdict, None, [], [96, 8], [], detector_details=details)
    assert syn.report_card["grade"] == "F"
