"""Tests para el nodo de acciones sugeridas."""

import pytest

from src.agent.nodes.actions import actions_node


@pytest.mark.asyncio
async def test_actions_generates_urgent_and_revision():
    state = {
        "processed_items": [
            {
                "external_id": "a1",
                "classification": {
                    "sentimiento": "Negativo",
                    "urgencia": "Alta",
                    "categorias": ["Pagos"],
                    "confianza": 0.95,
                    "resumen": "Fallo al pagar",
                },
            },
            {
                "external_id": "a2",
                "classification": {
                    "sentimiento": "Neutral",
                    "urgencia": "Baja",
                    "categorias": [],
                    "confianza": 0.5,
                    "resumen": "Mensaje ambiguo",
                },
            },
        ],
        "patterns": [
            {
                "descripcion": "Demoras en soporte",
                "frecuencia_estimada": "Alta",
                "nivel_impacto": "Alto",
            }
        ],
    }
    result = await actions_node(state)
    actions = result["actions"]
    tipos = {a["tipo"] for a in actions}
    assert "urgente" in tipos
    assert "revision" in tipos
    assert "patron" in tipos


@pytest.mark.asyncio
async def test_actions_opportunity_on_repeated_positive_category():
    state = {
        "processed_items": [
            {
                "external_id": "p1",
                "classification": {
                    "sentimiento": "Positivo",
                    "urgencia": "Baja",
                    "categorias": ["App"],
                    "confianza": 0.9,
                    "resumen": "Buena app",
                },
            },
            {
                "external_id": "p2",
                "classification": {
                    "sentimiento": "Positivo",
                    "urgencia": "Baja",
                    "categorias": ["App"],
                    "confianza": 0.92,
                    "resumen": "App rápida",
                },
            },
        ],
        "patterns": [],
    }
    result = await actions_node(state)
    assert any(a["tipo"] == "oportunidad" for a in result["actions"])


@pytest.mark.asyncio
async def test_actions_empty_when_no_data():
    result = await actions_node({"processed_items": [], "patterns": []})
    assert result["actions"] == []
