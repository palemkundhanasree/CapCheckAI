import pytest
from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.services.orchestrator import VerificationOrchestrator
from app.db.repositories.job_repository import JobRepository


@pytest.mark.asyncio
async def test_end_to_end_claim_verification(client: TestClient):
    db = SessionLocal()
    try:
        job_repo = JobRepository(db)
        job = job_repo.create_job(job_type="claim", input_data='{"claim_text": "Drinking disinfectant cures COVID-19."}')

        orchestrator = VerificationOrchestrator(db)
        report_id = await orchestrator.verify_claim(job.id, "Drinking disinfectant cures COVID-19.")

        assert report_id is not None

        # Fetch report via API
        response = client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert "overall_verdict" in data
        assert "evidence_items" in data
        assert len(data["evidence_items"]) > 0

        # Check PDF download endpoint
        pdf_res = client.get(f"/api/v1/reports/{report_id}/pdf")
        assert pdf_res.status_code == 200

        # Delete report via API
        del_res = client.delete(f"/api/v1/reports/{report_id}")
        assert del_res.status_code == 200

        # Verify it is gone
        get_again = client.get(f"/api/v1/reports/{report_id}")
        assert get_again.status_code == 404
    finally:
        db.close()
