from app.services.verdict_engine import VerdictEngine
from app.schemas.verdict import FactualVerdictType, MediaAuthenticityType


def test_verdict_engine_separates_claim_from_media():
    # An authentic photo accompanied by a false claim
    factual_verdict = FactualVerdictType.CONTRADICTED.value
    media_verdict = MediaAuthenticityType.AUTHENTIC.value

    synthesis = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=factual_verdict,
        media_verdict=media_verdict,
        context_verdict=None,
        evidence_items=[{"stance": "CONTRADICTS", "credibility_score": 90.0}],
        detector_scores=[10.0],
        indicators=[]
    )

    assert synthesis.factual_claim_verdict == FactualVerdictType.CONTRADICTED.value
    assert synthesis.media_authenticity_verdict == MediaAuthenticityType.AUTHENTIC.value
    assert "Contradicted" in synthesis.verdict_label


def test_evaluate_media_authenticity_thresholds():
    # High AI score
    high_ai = VerdictEngine.evaluate_media_authenticity(
        ai_score=85.0,
        manipulation_score=15.0,
        indicators=["Frequency artifact"]
    )
    assert high_ai == MediaAuthenticityType.AI_GENERATED.value

    # Low score
    authentic = VerdictEngine.evaluate_media_authenticity(
        ai_score=12.0,
        manipulation_score=8.0,
        indicators=[],
        has_provenance=True
    )
    assert authentic == MediaAuthenticityType.AUTHENTIC.value

    # Without camera data or Content Credentials, "no warning signs" is only "likely" authentic
    unproven = VerdictEngine.evaluate_media_authenticity(ai_score=12.0, manipulation_score=8.0, indicators=[])
    assert unproven == MediaAuthenticityType.LIKELY_AUTHENTIC.value


def test_correctness_percentage_for_claims():
    strong_false = [{"stance": "CONTRADICTS", "credibility_score": 90.0, "kind": "knowledge", "publisher": "Ref"}]
    pct, why = VerdictEngine.estimate_correctness("claim", strong_false, [], None, 80.0)
    assert pct is not None and pct <= 10 and "contradict" in why.lower() or "support" in why.lower()

    strong_true = [{"stance": "SUPPORTS", "credibility_score": 90.0, "kind": "knowledge", "publisher": "Ref"}]
    pct, _ = VerdictEngine.estimate_correctness("claim", strong_true, [], None, 80.0)
    assert pct >= 90

    # No decisive source: a percentage must not be invented
    pct, why = VerdictEngine.estimate_correctness("claim", [], [], None, 20.0)
    assert pct is None and "guess" in why


def test_correctness_percentage_for_media_is_capped():
    pct, _ = VerdictEngine.estimate_correctness("image", [], [5.0, 8.0], None, 90.0)
    assert pct == 88
    pct, _ = VerdictEngine.estimate_correctness("image", [], [96.0], None, 90.0)
    assert pct <= 4
