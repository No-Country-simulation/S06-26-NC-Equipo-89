import io
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.tools.supabase_client import get_db


@pytest.fixture
def client(mock_pool):
    pool, conn = mock_pool
    conn.execute = AsyncMock(return_value="INSERT 1")

    async def _override_get_db():
        return pool

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_ingest_csv_rejects_without_api_key(client):
    csv_content = "texto\nHola mundo\n"
    response = client.post(
        "/ingest/csv",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 401


def test_ingest_csv_parses_rows(client, api_key, mock_pool):
    pool, conn = mock_pool
    csv_content = "texto,fuente\nMensaje uno,csv\nMensaje dos,csv\n"
    response = client.post(
        "/ingest/csv",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["inserted"] == 2
    assert data["skipped"] == 0
    assert conn.execute.await_count == 2


def test_ingest_csv_requires_texto_column(client, api_key):
    csv_content = "fuente\nwhatsapp\n"
    response = client.post(
        "/ingest/csv",
        files={"file": ("bad.csv", csv_content, "text/csv")},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 400
    assert "texto" in response.json()["detail"].lower()


def test_ingest_csv_skips_empty_texto(client, api_key, mock_pool):
    pool, conn = mock_pool
    csv_content = "texto,fuente\n,csv\nHola,csv\n"
    response = client.post(
        "/ingest/csv",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["inserted"] == 1
    assert data["skipped"] == 1
