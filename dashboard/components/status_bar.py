"""Barra de contexto — última actualización, cola y auto-refresh."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from dashboard.components.pipeline_status import render as render_pipeline
from dashboard.components.worker_activity import render as render_worker_activity
from dashboard.health import check_fastapi_health
from dashboard.supabase_queries import get_last_activity_at, get_queue_health, get_worker_activity


def _format_relative(iso_ts: str) -> str:
    """Convierte timestamp ISO a texto relativo en español."""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - ts
        minutes = int(delta.total_seconds() // 60)
        if minutes < 1:
            return "hace un momento"
        if minutes < 60:
            return f"hace {minutes} min"
        hours = minutes // 60
        if hours < 24:
            return f"hace {hours} h"
        days = hours // 24
        return f"hace {days} d"
    except (ValueError, TypeError):
        return "desconocida"


def _clear_live_caches() -> None:
    get_queue_health.clear()
    get_worker_activity.clear()
    get_last_activity_at.clear()
    check_fastapi_health.clear()


def _render_content() -> None:
    """Contenido de la barra de estado."""
    render_worker_activity(show_delta=True)

    col_meta, col_pipe = st.columns([1.2, 1])
    with col_meta:
        try:
            last_at = get_last_activity_at()
            if last_at:
                st.caption(f"Última actividad en BD: {_format_relative(last_at)}")
            else:
                st.caption("Sin actividad registrada aún")
        except EnvironmentError:
            st.caption("Supabase no configurado")
        except Exception:
            st.caption("No se pudo obtener la última actualización")

    with col_pipe:
        render_pipeline(compact=True)


@st.fragment(run_every=30)
def _live_status_fragment() -> None:
    _clear_live_caches()
    _render_content()


def render() -> None:
    """Muestra barra de contexto; auto-refresh cada 30 s si está activo."""
    if st.session_state.get("fc_auto_refresh", True):
        _live_status_fragment()
    else:
        _render_content()
