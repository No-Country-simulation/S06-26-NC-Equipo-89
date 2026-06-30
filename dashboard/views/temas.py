"""Vista — Temas Recurrentes.

Combina análisis estadístico de categorías históricas (Parte A)
con resumen semántico del LLM (Parte B).
"""
from __future__ import annotations

import streamlit as st

from dashboard.components import temas as temas_component
from dashboard.layout import render_page_header
from dashboard.supabase_queries import get_temas_recurrentes


def render() -> None:
    render_page_header("temas")

    st.markdown(
        "El agente analiza las categorías que reaparecen con mayor frecuencia en el período "
        "seleccionado y agrega inteligencia semántica del LLM para detectar variantes del mismo "
        "problema (ej: *'falla QR'* y *'error tarjeta'* son el mismo tema de **Pagos**)."
    )

    col_refresh, col_hint = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Actualizar", key="temas_refresh"):
            get_temas_recurrentes.clear()
            st.rerun()
    with col_hint:
        st.caption(
            "El worker actualiza este análisis automáticamente cada día. "
            "Podés forzar una actualización con el botón."
        )

    st.divider()

    try:
        data = get_temas_recurrentes()
    except Exception as exc:
        st.error(f"Error al cargar temas recurrentes: {exc}")
        return

    temas_component.render(data)
