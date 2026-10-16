import sys
sys.path.insert(0, 'backend')
import asyncio
from app.db.session import SessionLocal
from app.services.orchestrator import VerificationOrchestrator
from app.db.repositories.job_repository import JobRepository
from app.db.repositories.report_repository import ReportRepository

async def test_url():
    db = SessionLocal()
    try:
        job_repo = JobRepository(db)
        report_repo = ReportRepository(db)
        orchestrator = VerificationOrchestrator(db)

        # 1. Test Suspicious Link (Local/Private IP)
        suspicious_url = "http://192.168.1.1/admin-panel"
        job1 = job_repo.create_job(job_type="url", input_data=suspicious_url, user_id=None)
        print(f"Created job {job1.id} for suspicious URL: {suspicious_url}", flush=True)

        report_id1 = await orchestrator.verify_url(job1.id, suspicious_url)
        report1 = report_repo.get_report_by_id(report_id1)
        job1_status = job_repo.get_job_by_id(job1.id)

        print(f"Job1 status: {job1_status.status}", flush=True)
        print(f"Report1 verdict: {report1.overall_verdict} | label: {report1.verdict_label}", flush=True)
        assert job1_status.status == "completed"
        assert "0.0%" in report1.verdict_label
        assert report1.overall_verdict == "CONTRADICTED"

        # 2. Test Invalid / Unresolvable Domain
        unresolvable_url = "https://invalid-nonexistent-domain-test-123456789.org/news/sample"
        job2 = job_repo.create_job(job_type="url", input_data=unresolvable_url, user_id=None)
        print(f"\nCreated job {job2.id} for unresolvable URL: {unresolvable_url}", flush=True)

        report_id2 = await orchestrator.verify_url(job2.id, unresolvable_url)
        report2 = report_repo.get_report_by_id(report_id2)
        job2_status = job_repo.get_job_by_id(job2.id)

        print(f"Job2 status: {job2_status.status}", flush=True)
        print(f"Report2 verdict: {report2.overall_verdict} | label: {report2.verdict_label}", flush=True)
        assert job2_status.status == "completed"
        assert "0.0%" in report2.verdict_label or "Fails" in report2.summary

        print("\n>>> ALL URL VERIFICATION & RESILIENCE TESTS PASSED! NO FROZEN JOBS! <<<", flush=True)

    finally:
        db.close()

asyncio.run(test_url())
