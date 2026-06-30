import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("DB_DSN", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")


class _AsyncCM:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def api_key():
    # Debe coincidir con settings.api_key (env API_KEY), tanto en local como en CI.
    return os.environ.get("API_KEY", "test-api-key")


@pytest.fixture
def mock_pool():
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="INSERT 1")
    conn.fetch = AsyncMock(return_value=[])
    conn.executemany = AsyncMock()
    conn.transaction = MagicMock(return_value=_AsyncCM(conn))

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncCM(conn))
    pool.execute = AsyncMock(return_value="INSERT 1")
    return pool, conn


@pytest.fixture
def sample_payload():
    return {
        "external_id": "test-001",
        "fuente": "whatsapp",
        "texto": "La app no funciona",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }
