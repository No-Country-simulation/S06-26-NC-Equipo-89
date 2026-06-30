"""Tests unitarios para consistency_check — sin llamadas reales al LLM."""
from __future__ import annotations

from collections import Counter
from unittest.mock import AsyncMock, patch

import pytest

# Importamos las funciones internas directamente
from scripts.consistency_check import (
    _field_stability,
    _majority,
    run_consistency_check,
)


# ── Helpers internos ──────────────────────────────────────────────────────────

def test_field_stability_total():
    assert _field_stability(["A", "A", "A"]) == 100.0


def test_field_stability_partial():
    assert _field_stability(["A", "A", "B"]) == pytest.approx(66.7, abs=0.1)


def test_field_stability_empty():
    assert _field_stability([]) == 0.0


def test_majority_returns_most_common():
    assert _majority(["A", "A", "B"]) == "A"


def test_majority_empty():
    assert _majority([]) == ""


# ── run_consistency_check con LLM mockeado ────────────────────────────────────

def _make_classify_outcome(sentimiento: str, urgencia: str, categorias: list[str], confianza: float) -> dict:
    return {
        "status": "success",
        "classification": {
            "sentimiento": sentimiento,
            "urgencia": urgencia,
            "categorias": categorias,
            "confianza": confianza,
            "resumen": "test",
        },
    }


@pytest.mark.asyncio
async def test_stable_model_reports_high_stability():
    """Cuando el modelo siempre responde igual, estabilidad = 100%."""
    outcome = _make_classify_outcome("Negativo", "Alta", ["App", "Pagos"], 0.9)
    with patch("scripts.consistency_check.classify_single", new=AsyncMock(return_value=outcome)):
        summary = await run_consistency_check(
            runs=3,
            save_metrics=False,
            mark_unstable=False,
            stability_threshold=0.70,
        )
    assert summary["estabilidad_promedio"] == 100.0
    assert summary["inestables"] == []


@pytest.mark.asyncio
async def test_unstable_model_reported_as_inestable():
    """Cuando urgencia varía, el mensaje debe quedar en inestables."""
    urgencias = ["Alta", "Media", "Alta"]
    call_count = 0

    async def mock_classify(item, system, **kwargs):
        nonlocal call_count
        urg = urgencias[call_count % len(urgencias)]
        call_count += 1
        return _make_classify_outcome("Negativo", urg, ["App"], 0.75)

    with patch("scripts.consistency_check.classify_single", new=mock_classify):
        summary = await run_consistency_check(
            runs=3,
            save_metrics=False,
            mark_unstable=False,
            stability_threshold=0.90,  # umbral alto para que urgencia 66% falle
        )
    # urgencia: 2/3 Alta = 66.7% → inestable con threshold 0.90
    assert len(summary["inestables"]) > 0


@pytest.mark.asyncio
async def test_summary_structure():
    """El dict de salida tiene todas las claves esperadas."""
    outcome = _make_classify_outcome("Positivo", "Baja", ["Atención al Cliente"], 0.85)
    with patch("scripts.consistency_check.classify_single", new=AsyncMock(return_value=outcome)):
        summary = await run_consistency_check(
            runs=2,
            save_metrics=False,
            mark_unstable=False,
            stability_threshold=0.70,
        )
    assert summary["tipo"] == "consistency_run"
    assert summary["runs"] == 2
    assert "total" in summary
    assert "estabilidad_promedio" in summary
    assert "exact_match_pct" in summary
    assert "por_campo" in summary
    assert set(summary["por_campo"].keys()) == {"sentimiento", "urgencia", "categorias"}
    for campo_data in summary["por_campo"].values():
        assert "estabilidad" in campo_data
        assert "exactitud" in campo_data
    assert "inestables" in summary


@pytest.mark.asyncio
async def test_error_runs_not_counted():
    """Los runs con error se omiten sin romper el cálculo."""
    call_count = 0

    async def mock_with_error(item, system, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 3 == 0:
            return {"status": "error", "error": "timeout"}
        return _make_classify_outcome("Negativo", "Alta", ["App"], 0.8)

    with patch("scripts.consistency_check.classify_single", new=mock_with_error):
        summary = await run_consistency_check(
            runs=3,
            save_metrics=False,
            mark_unstable=False,
            stability_threshold=0.70,
        )
    # No debe lanzar excepción y debe tener resultados
    assert summary["total"] > 0
    assert summary["estabilidad_promedio"] >= 0
