"""Tests para queries y helpers del dashboard."""

from unittest.mock import MagicMock, patch

import pytest

from dashboard.components.ui import source_badge
from dashboard.health import check_fastapi_health


def test_source_badge_whatsapp():
    html = source_badge("whatsapp")
    assert "WhatsApp" in html
    assert "fc-badge" in html


def test_source_badge_unknown():
    html = source_badge("telegram")
    assert "telegram" in html


def test_confidence_badge_low():
    from dashboard.components.feedback_card import _confidence_badge

    html = _confidence_badge(0.55)
    assert "revisar" in html
    assert "55" in html


def test_confidence_badge_high():
    from dashboard.components.feedback_card import _confidence_badge

    html = _confidence_badge(0.92)
    assert "92" in html
    assert "revisar" not in html


@patch("dashboard.supabase_queries.get_client")
def test_get_urgencia_distribucion(mock_get_client):
    from dashboard.supabase_queries import get_urgencia_distribucion

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_res = MagicMock()
    mock_res.data = [
        {"urgencia": "Alta"},
        {"urgencia": "Alta"},
        {"urgencia": "Media"},
        {"urgencia": "Baja"},
    ]
    mock_client.table.return_value.select.return_value.execute.return_value = mock_res

    get_urgencia_distribucion.clear()
    result = get_urgencia_distribucion()
    assert {r["urgencia"]: r["cantidad"] for r in result} == {
        "Alta": 2,
        "Media": 1,
        "Baja": 1,
    }


@patch("dashboard.health.httpx.get")
def test_check_fastapi_health_ok(mock_get):
    check_fastapi_health.clear()
    mock_get.return_value = MagicMock(status_code=200)
    ok, msg = check_fastapi_health()
    assert ok is True
    assert "operativo" in msg


@patch("dashboard.health.httpx.get")
def test_check_fastapi_health_connect_error(mock_get):
    import httpx

    check_fastapi_health.clear()
    mock_get.side_effect = httpx.ConnectError("fail")
    ok, msg = check_fastapi_health()
    assert ok is False
    assert "8000" in msg


@patch("dashboard.supabase_queries.get_client")
def test_get_pending_count(mock_get_client):
    from dashboard.supabase_queries import get_pending_count, get_queue_health

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    pending_res = MagicMock()
    pending_res.count = 5
    processing_res = MagicMock()
    processing_res.count = 0
    error_res = MagicMock()
    error_res.count = 0
    mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        pending_res,
        processing_res,
        error_res,
    ]

    get_queue_health.clear()
    assert get_pending_count() == 5


@patch("dashboard.supabase_queries.get_client")
def test_get_queue_health(mock_get_client):
    from dashboard.supabase_queries import get_queue_health

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    pending_res = MagicMock()
    pending_res.count = 3
    processing_res = MagicMock()
    processing_res.count = 2
    error_res = MagicMock()
    error_res.count = 1
    mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        pending_res,
        processing_res,
        error_res,
    ]

    get_queue_health.clear()
    assert get_queue_health() == {"pendientes": 3, "procesando": 2, "errores": 1}


@patch("dashboard.supabase_queries.get_client")
def test_get_last_activity_at(mock_get_client):
    from dashboard.supabase_queries import get_last_activity_at

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    raw_res = MagicMock()
    raw_res.data = [{"created_at": "2026-06-10T10:00:00Z"}]
    clas_res = MagicMock()
    clas_res.data = [{"created_at": "2026-06-15T12:00:00Z"}]
    metricas_res = MagicMock()
    metricas_res.data = [{"created_at": "2026-06-14T08:00:00Z"}]

    mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.side_effect = [
        raw_res,
        clas_res,
        metricas_res,
    ]

    get_last_activity_at.clear()
    assert get_last_activity_at() == "2026-06-15T12:00:00Z"


@patch("dashboard.supabase_queries.get_ultimo_lote_metricas")
@patch("dashboard.supabase_queries.get_queue_health")
@patch("dashboard.supabase_queries.get_client")
def test_get_worker_activity(mock_get_client, mock_queue, mock_ultimo):
    from dashboard.supabase_queries import get_worker_activity

    mock_queue.return_value = {"pendientes": 2, "procesando": 0, "errores": 5}
    mock_ultimo.return_value = {
        "created_at": "2026-06-16T12:00:00+00:00",
        "datos": {
            "total_procesados": 0,
            "errores_en_lote": 50,
            "tamano_lote": 50,
        },
    }
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    clas_res = MagicMock()
    clas_res.count = 0
    mock_client.table.return_value.select.return_value.gte.return_value.execute.return_value = clas_res

    get_worker_activity.clear()
    activity = get_worker_activity()
    assert activity["errores_ultimo_ciclo"] == 50
    assert activity["tamano_ultimo_ciclo"] == 50
    assert activity["estado_agente"] in ("ciclo_reciente", "en_espera")


def test_count_skipped_rows():
    from dashboard.components.loaders import count_skipped_rows

    raw = b"texto,fuente\n,csv\nValido,csv\n"
    assert count_skipped_rows("datos.csv", raw) == 1


def test_sample_csv_template():
    from dashboard.components.loaders import sample_csv_template

    content = sample_csv_template().decode()
    assert "texto" in content
    assert "ejemplo-001" in content


@patch("dashboard.supabase_queries._latest_tick_id_con_patrones", return_value="tick-abc")
@patch("dashboard.supabase_queries.get_client")
def test_get_patrones_filters_by_latest_tick(mock_get_client, _mock_tick):
    from dashboard.supabase_queries import get_patrones

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    patrones_res = MagicMock()
    patrones_res.data = [{"descripcion": "Demoras", "tick_id": "tick-abc"}]

    select_chain = mock_client.table.return_value.select.return_value
    order_chain = select_chain.order.return_value
    eq_chain = order_chain.eq.return_value
    eq_chain.execute.return_value = patrones_res

    get_patrones.clear()
    result = get_patrones(latest_tick_only=True)
    assert len(result) == 1
    order_chain.eq.assert_called_with("tick_id", "tick-abc")
