from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.tools.supabase_client import get_db


@pytest.fixture
def client(mock_pool):
    pool, _ = mock_pool

    async def _override_get_db():
        return pool

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_deep_ok(client, mock_pool):
    pool, conn = mock_pool
    conn.fetchval = AsyncMock(return_value=1)

    async def _get_db():
        return pool

    with patch("src.api.main.get_db", _get_db):
        response = client.get("/health/deep")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_ingest_rejects_without_api_key(client, sample_payload):
    response = client.post("/ingest", json=sample_payload)
    assert response.status_code == 401


def test_ingest_rejects_invalid_api_key(client, sample_payload, api_key):
    response = client.post(
        "/ingest",
        json=sample_payload,
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_ingest_accepts_valid_payload(client, sample_payload, api_key, mock_pool):
    pool, conn = mock_pool
    response = client.post(
        "/ingest",
        json=sample_payload,
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "success"
    pool.execute.assert_called_once()


def test_ingest_validates_pydantic(client, api_key):
    response = client.post(
        "/ingest",
        json={"fuente": "whatsapp"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 422
