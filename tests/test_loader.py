import pytest
from unittest.mock import AsyncMock, patch

from src.agent.nodes.loader import loader_node


@pytest.mark.asyncio
async def test_loader_empty_batch(mock_pool):
    pool, conn = mock_pool
    conn.fetch = AsyncMock(return_value=[])

    with patch("src.agent.nodes.loader.get_db", AsyncMock(return_value=pool)):
        result = await loader_node({"current_batch": []})

    assert result["current_batch"] == []
    conn.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_loader_returns_batch_and_resets_state(mock_pool):
    pool, conn = mock_pool
    record = {
        "id": 1,
        "external_id": "ext-1",
        "fuente": "whatsapp",
        "texto": "Hola",
        "timestamp": None,
        "metadata": {},
    }
    conn.fetch = AsyncMock(return_value=[record])

    with patch("src.agent.nodes.loader.get_db", AsyncMock(return_value=pool)):
        result = await loader_node({"current_batch": []})

    assert len(result["current_batch"]) == 1
    assert result["current_batch"][0]["external_id"] == "ext-1"
    assert result["processed_items"] == []
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_loader_uses_skip_locked_query(mock_pool):
    pool, conn = mock_pool
    conn.fetch = AsyncMock(return_value=[])

    with patch("src.agent.nodes.loader.get_db", AsyncMock(return_value=pool)):
        await loader_node({})

    query = conn.fetch.await_args[0][0]
    assert "SKIP LOCKED" in query
    assert "estado = 'pendiente'" in query
