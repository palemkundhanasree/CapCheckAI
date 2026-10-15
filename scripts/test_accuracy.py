import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import asyncio
from app.db.session import SessionLocal
from app.services.orchestrator import VerificationOrchestrator
from app.db.repositories.report_repository import ReportRepository

async def run_tests():
    db = SessionLocal()
    try:
        orch = VerificationOrchestrator(db)
        repo = ReportRepository(db)
        
        # Test 1: True claim
        job1 = orch.job_repo.create_job("claim", "{}")
        rep1_id = await orch.verify_claim(job1.id, "The capital of France is Paris")
        rep1 = repo.get_report_by_id(rep1_id)
        print("Test 1 (Capital of France):", rep1.overall_verdict, "->", rep1.verdict_label)

        # Test 2: False claim
        job2 = orch.job_repo.create_job("claim", "{}")
        rep2_id = await orch.verify_claim(job2.id, "The Earth is flat")
        rep2 = repo.get_report_by_id(rep2_id)
        print("Test 2 (Flat Earth):", rep2.overall_verdict, "->", rep2.verdict_label)

        # Test 3: True science claim
        job3 = orch.job_repo.create_job("claim", "{}")
        rep3_id = await orch.verify_claim(job3.id, "The Earth orbits around the Sun")
        rep3 = repo.get_report_by_id(rep3_id)
        print("Test 3 (Earth orbits Sun):", rep3.overall_verdict, "->", rep3.verdict_label)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
