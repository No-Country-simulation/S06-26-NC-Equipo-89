"""Barra de contexto — última actualización y cola pendiente."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from dashboard.supabase_queries import get_last_activity_at, get_queue_health


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


def render() -> None:
    """Muestra última actividad y badge de pendientes."""
    parts: list[str] = []

    try:
        last_at = get_last_activity_at()
        if last_at:
            parts.append(f"Última actualización: {_format_relative(last_at)}")
        else:
            parts.append("Sin actividad registrada aún")
    except EnvironmentError:
        parts.append("Supabase no configurado")
    except Exception:
        parts.append("No se pudo obtener la última actualización")

    try:
        health = get_queue_health()
        pending = health["pendientes"]
        if pending > 0:
            parts.append(f"⏳ {pending} en cola")
        errors = health["errores"]
        if errors > 0:
            parts.append(f"⚠ {errors} con error")
    except Exception:
        pass

    if parts:
        st.caption(" · ".join(parts))
