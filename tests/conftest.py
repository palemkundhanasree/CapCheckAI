import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    init_db()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
