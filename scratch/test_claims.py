import sys
sys.path.insert(0, 'backend')
import asyncio
from app.engines.news.factcheck_client import search_curated_factchecks
from app.engines.news.search_client import search_web_evidence
from app.services.evidence_evaluator import EvidenceEvaluatorService
from app.services.verdict_engine import VerdictEngine

async def test_claim(claim):
    print(f"\n--- Testing Claim: '{claim}' ---")
    curated = search_curated_factchecks(claim)
    web = await search_web_evidence(claim)
    all_ev = curated + web
    scored = EvidenceEvaluatorService.evaluate_and_rank_evidence(claim, all_ev)
    for s in scored[:3]:
        print(f"  Source: {s.get('source_name')} | Stance: {s.get('stance')} | Score: {s.get('credibility_score')} | Title: {s.get('title')[:40]}")
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
    print(f"  Result: {synthesis.overall_verdict} | Label: {synthesis.verdict_label}")

async def main():
    await test_claim("modi married sonia")
    await test_claim("Gandhi Killed Godse")
    await test_claim("Godse killed Gandhi")
    await test_claim("The Earth orbits around the Sun")

asyncio.run(main())
