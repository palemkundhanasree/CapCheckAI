from fastapi.testclient import TestClient


def test_submit_claim_verification(client: TestClient):
    payload = {
        "claim_text": "Drinking disinfectant or bleach is a medical cure for coronavirus infections.",
        "context": "Viral posts on Twitter"
    }
    response = client.post("/api/v1/verify/claim", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["job_type"] == "claim"
    assert data["status"] in ("queued", "processing", "completed")


def test_submit_claim_too_short(client: TestClient):
    payload = {"claim_text": "Hi"}
    response = client.post("/api/v1/verify/claim", json=payload)
    assert response.status_code == 422  # Pydantic validation error
