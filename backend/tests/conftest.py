import os
import sys
import tempfile
from pathlib import Path

import pytest

# Use a throwaway SQLite database and no external API keys for every test run.
# These must be set before the app modules are imported.
_tmp = tempfile.mkdtemp(prefix="krishiveda-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"
for key in ("OPENWEATHER_API_KEY", "DATA_GOV_IN_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "EXPERT_ACCESS_CODE"):
    os.environ[key] = ""

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import weather_service  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture(autouse=True)
def clear_weather_cache():
    weather_service._cache.clear()
    yield
    weather_service._cache.clear()


@pytest.fixture
def farmer(client):
    resp = client.post("/api/farmers", json={
        "name": "Test Farmer",
        "phone": "9876543210",
        "preferred_language": "hi",
        "state": "Punjab",
        "district": "Ludhiana",
        "farm": {"name": "North field", "location_name": "Ludhiana", "area_acres": 2.5,
                 "soil_type": "alluvial", "crops": [{"crop_name": "Wheat", "season": "rabi"}]},
    })
    assert resp.status_code == 201, resp.text
    return resp.json()
