"""Tests para tick_id compartido en persister."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.nodes.persister import persister_node


class _AsyncCM:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_persister_uses_same_tick_id_for_metricas_and_patrones():
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    conn.transaction = MagicMock(return_value=_AsyncCM(conn))
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncCM(conn))

    state = {
        "current_batch": [{"external_id": "x1"}],
        "processed_items": [
            {
                "external_id": "x1",
                "classification": {
                    "sentimiento": "Negativo",
                    "urgencia": "Alta",
                    "idioma": "es",
                    "categorias": ["soporte"],
                    "confianza": 0.9,
                    "resumen": "Problema",
                },
            }
        ],
        "errors": [],
        "patterns": [
            {"descripcion": "Demoras", "frecuencia_estimada": 5, "nivel_impacto": "Alto"},
        ],
        "metrics": {"total": 1, "negativos": 1},
        "actions": [],
    }

    tick_ids: list = []

    async def capture_execute(query, *args):
        if "feedback_metricas" in query:
            tick_ids.append(args[1])

    async def capture_executemany(query, records):
        if "feedback_patrones" in query:
            for row in records:
                tick_ids.append(row[3])

    conn.execute = AsyncMock(side_effect=capture_execute)
    conn.executemany = AsyncMock(side_effect=capture_executemany)

    with patch("src.agent.nodes.persister.get_db", new_callable=AsyncMock, return_value=pool):
        await persister_node(state)

    assert len(tick_ids) == 2
    assert tick_ids[0] == tick_ids[1]


@pytest.mark.asyncio
async def test_persister_upsert_clasificado_sql():
    conn = AsyncMock()
    conn.executemany = AsyncMock()
    conn.transaction = MagicMock(return_value=_AsyncCM(conn))
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncCM(conn))

    state = {
        "current_batch": [{"external_id": "x1"}],
        "processed_items": [
            {
                "external_id": "x1",
                "classification": {
                    "sentimiento": "Neutral",
                    "urgencia": "Baja",
                    "idioma": "es",
                    "categorias": [],
                    "confianza": 0.8,
                    "resumen": "Ok",
                },
            }
        ],
        "errors": [],
        "patterns": [],
        "metrics": {},
        "actions": [],
    }

    with patch("src.agent.nodes.persister.get_db", new_callable=AsyncMock, return_value=pool):
        await persister_node(state)

    sql = conn.executemany.await_args[0][0]
    assert "ON CONFLICT (external_id) DO UPDATE" in sql
