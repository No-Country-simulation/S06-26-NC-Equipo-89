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
    error_res = MagicMock()
    error_res.count = 0
    mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        pending_res,
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
    error_res = MagicMock()
    error_res.count = 2
    mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        pending_res,
        error_res,
    ]

    get_queue_health.clear()
    assert get_queue_health() == {"pendientes": 3, "errores": 2}


@patch("dashboard.supabase_queries.get_client")
def test_get_last_activity_at(mock_get_client):
    from dashboard.supabase_queries import get_last_activity_at

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    raw_res = MagicMock()
    raw_res.data = [{"created_at": "2026-06-10T10:00:00Z"}]
    clas_res = MagicMock()
    clas_res.data = [{"created_at": "2026-06-15T12:00:00Z"}]

    mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.side_effect = [
        raw_res,
        clas_res,
    ]

    get_last_activity_at.clear()
    assert get_last_activity_at() == "2026-06-15T12:00:00Z"


def test_count_skipped_rows():
    from dashboard.components.loaders import count_skipped_rows

    raw = b"texto,fuente\n,csv\nValido,csv\n"
    assert count_skipped_rows("datos.csv", raw) == 1


def test_sample_csv_template():
    from dashboard.components.loaders import sample_csv_template

    content = sample_csv_template().decode()
    assert "texto" in content
    assert "ejemplo-001" in content
