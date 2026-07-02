"""Vista compuesta — Temas recurrentes y patrones detectados."""

from __future__ import annotations

import streamlit as st

from dashboard.components import patrones
from dashboard.components import temas as temas_component
from dashboard.layout import render_page_header
from dashboard.supabase_queries import get_temas_recurrentes


def _render_temas_tab() -> None:
    st.caption(
        "Categorías que más repite el clasificador en el período, "
        "con conteos y tendencia."
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


def render() -> None:
    render_page_header("tendencias")

    tab_temas, tab_patrones = st.tabs(["Temas", "Patrones"])

    with tab_temas:
        _render_temas_tab()

    with tab_patrones:
        patrones.render()
