from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def test_copilot_rejects_without_api_key(client):
    response = client.post("/copilot/ask", json={"question": "¿Cuáles son los temas principales?"})
    assert response.status_code == 401


def test_copilot_ask_with_mocks(client, api_key, mock_pool):
    pool, conn = mock_pool
    conn.fetch = AsyncMock(
        return_value=[
            {
                "external_id": "ext-1",
                "texto": "La app falla",
                "sentimiento": "Negativo",
                "urgencia": "Alta",
                "categorias": '["Técnico"]',
                "similarity": 0.92,
            }
        ]
    )

    with (
        patch("src.api.routes.copilot.get_db", AsyncMock(return_value=pool)),
        patch(
            "src.api.routes.copilot.cohere_client.embed_query",
            AsyncMock(return_value=[0.1] * 1024),
        ),
        patch(
            "src.api.routes.copilot.generate_text",
            AsyncMock(return_value="Los clientes reportan fallas técnicas."),
        ),
    ):
        response = client.post(
            "/copilot/ask",
            json={"question": "¿Qué problemas reportan los usuarios?"},
            headers={"X-API-Key": api_key},
        )

    assert response.status_code == 200
    data = response.json()
    assert "fallas" in data["answer"].lower() or "técnic" in data["answer"].lower()
    assert len(data["sources"]) == 1
    assert data["sources"][0]["external_id"] == "ext-1"


def test_copilot_empty_results(client, api_key, mock_pool):
    pool, conn = mock_pool
    conn.fetch = AsyncMock(return_value=[])

    with (
        patch("src.api.routes.copilot.get_db", AsyncMock(return_value=pool)),
        patch(
            "src.api.routes.copilot.cohere_client.embed_query",
            AsyncMock(return_value=[0.1] * 1024),
        ),
    ):
        response = client.post(
            "/copilot/ask",
            json={"question": "¿Algo?"},
            headers={"X-API-Key": api_key},
        )

    assert response.status_code == 200
    assert "No encontré" in response.json()["answer"]
    assert response.json()["sources"] == []
