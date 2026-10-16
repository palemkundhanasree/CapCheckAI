import sys
sys.path.insert(0, 'backend')
from app.engines.news.claim_matcher import compute_evidence_stance, match_and_score_evidence
from app.engines.news.factcheck_client import search_curated_factchecks
from app.services.verdict_engine import VerdictEngine

def test_single_claim(claim, mock_evidence):
    scored = match_and_score_evidence(claim, mock_evidence)
    verdict = VerdictEngine.evaluate_claim_verdict(scored)
    synthesis = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict,
        media_verdict=None,
        context_verdict=None,
        evidence_items=scored,
        detector_scores=[],
        indicators=[]
    )
    print(f"\nClaim: '{claim}'")
    for s in scored[:2]:
        print(f"  Source: {s.get('source_name')} | Stance: {s.get('stance')} | Score: {s.get('credibility_score')}")
    print(f"  => Overall Verdict: {synthesis.overall_verdict} | Label: {synthesis.verdict_label}")
    return synthesis

# 1. Test Fabricated Marriage: "modi married sonia"
mock_modi_sonia = [
    {
        "title": "Wikipedia: Sonia Gandhi",
        "source_name": "Wikipedia",
        "snippet": "Sonia Gandhi is an Italian-born Indian politician. She married Rajiv Gandhi in 1968 and served as president of the Indian National Congress.",
        "credibility_score": 88.0,
        "stance": "NEUTRAL"
    },
    {
        "title": "Wikipedia: Narendra Modi",
        "source_name": "Wikipedia",
        "snippet": "Narendra Damodardas Modi is an Indian politician serving as the 14th prime minister of India since May 2014.",
        "credibility_score": 88.0,
        "stance": "NEUTRAL"
    }
]
res1 = test_single_claim("modi married sonia", mock_modi_sonia)
assert "0.0%" in res1.verdict_label or "CONTRADICTED" in res1.overall_verdict or "UNVERIFIED" in res1.overall_verdict or "False" in res1.verdict_label

# 2. Test Reversed Assassination: "Gandhi Killed Godse"
mock_gandhi_godse = [
    {
        "title": "Wikipedia: Nathuram Godse",
        "source_name": "Wikipedia",
        "snippet": "Nathuram Vinayak Godse assassinated Mahatma Gandhi, shooting him in the chest three times at point-blank range on 30 January 1948 in New Delhi.",
        "credibility_score": 88.0,
        "stance": "NEUTRAL"
    }
]
res2 = test_single_claim("Gandhi Killed Godse", mock_gandhi_godse)
assert res2.overall_verdict == "FALSE" or "0.0%" in res2.verdict_label

# 3. Test Historical Fact: "Godse killed Gandhi"
res3 = test_single_claim("Godse killed Gandhi", mock_gandhi_godse)
assert "100.0%" in res3.verdict_label or "SUPPORTED" in res3.overall_verdict

# 4. Test Curated Science: "The Earth orbits around the Sun"
curated_earth = search_curated_factchecks("The Earth orbits around the Sun")
res4 = test_single_claim("The Earth orbits around the Sun", curated_earth)
assert "SUPPORTED" in res4.overall_verdict

# 5. Test Negation / Contradiction: "Moon is the artificial satellite of the earth"
curated_moon = search_curated_factchecks("Moon is the artificial satellite of the earth")
res5 = test_single_claim("Moon is the artificial satellite of the earth", curated_moon)
assert res5.overall_verdict == "FALSE" or "0.0%" in res5.verdict_label

print("\n>>> ALL CLAIM VERIFICATION LOGIC TESTS PASSED SUCCESSFULLY! <<<")
