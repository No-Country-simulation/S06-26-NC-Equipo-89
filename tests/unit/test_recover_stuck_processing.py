"""Tests para recovery de mensajes atascados en procesando."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.queue_maintenance import recover_stuck_processing


class _AsyncCM:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_recover_stuck_processing_returns_count():
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="UPDATE 3")
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncCM(conn))

    with patch("src.core.queue_maintenance.get_db", new_callable=AsyncMock, return_value=pool):
        count = await recover_stuck_processing(stale_minutes=30)

    assert count == 3
    conn.execute.assert_awaited_once()
    args = conn.execute.await_args[0]
    assert args[1] == "30"


@pytest.mark.asyncio
async def test_recover_stuck_processing_zero_updates():
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="UPDATE 0")
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncCM(conn))

    with patch("src.core.queue_maintenance.get_db", new_callable=AsyncMock, return_value=pool):
        count = await recover_stuck_processing()

    assert count == 0
