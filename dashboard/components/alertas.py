"""Alertas in-app derivadas de KPIs y patrones."""

from __future__ import annotations

import streamlit as st

from dashboard.supabase_queries import get_alertas


def render(*, compact: bool = False) -> None:
    """Muestra alertas operativas en la vista general."""
    try:
        alertas = get_alertas()
    except Exception:
        return

    if not alertas:
        if not compact:
            st.caption("Sin alertas activas.")
        return

    for alert in alertas:
        nivel = alert.get("nivel", "info")
        titulo = alert.get("titulo", "")
        detalle = alert.get("detalle", "")
        msg = f"**{titulo}** — {detalle}" if detalle else f"**{titulo}**"
        if nivel == "error":
            st.error(msg)
        elif nivel == "warning":
            st.warning(msg)
        else:
            st.info(msg)
