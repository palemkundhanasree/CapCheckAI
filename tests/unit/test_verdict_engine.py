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
        indicators=[]
    )
    assert authentic == MediaAuthenticityType.AUTHENTIC.value
