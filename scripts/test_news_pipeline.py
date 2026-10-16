import sys
import os
from pathlib import Path
import asyncio

sys.path.insert(0, os.path.abspath('backend'))

from app.db.session import SessionLocal
from app.db.models import User, Report, VerificationJob
from app.services.orchestrator import VerificationOrchestrator
from app.engines.news.article_extractor import extract_article_content, infer_metadata_from_url
from app.security.url_safety import validate_url_safety


def test_url_normalization():
    u1 = validate_url_safety("bbc.com/news/world-europe-12345")
    assert u1.startswith("https://"), f"Expected https:// prefix, got: {u1}"
    print(f"[PASS] URL validation auto-prefixed: {u1}")

    u2 = validate_url_safety("https://www.reuters.com/business/tech")
    assert u2 == "https://www.reuters.com/business/tech"
    print(f"[PASS] Valid https URL accepted: {u2}")


def test_metadata_inference():
    inferred = infer_metadata_from_url("https://www.reuters.com/world/europe/france-announces-new-space-mission-2024")
    assert "France Announces New Space Mission" in inferred["title"]
    assert inferred["publisher"] == "Reuters"
    print(f"[PASS] Inferred title: '{inferred['title']}', Publisher: '{inferred['publisher']}'")


async def test_resilient_extraction():
    # Test with a non-existent or blocked URL
    res = await extract_article_content("https://example-blocked-server.org/news/breaking-scientific-discovery-2024")
    assert res["title"]
    assert res["body_text"]
    assert res["publisher"]
    assert res["extraction_status"] == "fallback"
    print(f"[PASS] Resilient extraction fallback succeeded: '{res['title']}' ({res['publisher']})")


async def test_verify_url_pipeline():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        orch = VerificationOrchestrator(db)
        
        # Test sample NASA news URL
        test_url = "https://solarsystem.nasa.gov/planets/earth/overview/"
        job = orch.job_repo.create_job(job_type="url", input_data='{"url": "' + test_url + '"}', user_id=user.id)
        
        print(f"Executing verify_url pipeline for job {job.id}...")
        report_id = await orch.verify_url(job.id, test_url)
        assert report_id, "verify_url did not return a report ID"
        
        rep = orch.report_repo.get_report_by_id(report_id)
        assert rep, "Report was not found in database"
        assert rep.input_type == "url", f"Unexpected input_type: {rep.input_type}"
        assert "Accuracy Level of Real:" in rep.verdict_label, f"Missing accuracy format: {rep.verdict_label}"
        assert len(rep.evidence_items) > 0, "No evidence items populated"
        
        print(f"[PASS] verify_url pipeline completed successfully!")
        print(f"       Dossier ID: {rep.id}")
        print(f"       Headline: {rep.title}")
        print(f"       Verdict: {rep.verdict_label}")
        print(f"       Evidence Count: {len(rep.evidence_items)}")
        for idx, ev in enumerate(rep.evidence_items[:3], 1):
            print(f"         {idx}. [{ev.stance}] {ev.source_name} - {ev.title[:45]} ({ev.credibility_score}%)")
        
        # Clean up test report
        db.delete(rep)
        db.delete(job)
        db.commit()
    finally:
        db.close()


async def main():
    print("=== Testing News & URL Verification Engine ===")
    test_url_normalization()
    test_metadata_inference()
    await test_resilient_extraction()
    await test_verify_url_pipeline()
    print("\nALL NEWS ENGINE VERIFICATIONS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
