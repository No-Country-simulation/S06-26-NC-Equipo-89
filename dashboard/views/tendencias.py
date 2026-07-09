"""Vista compuesta — Temas recurrentes y patrones detectados."""

from __future__ import annotations

import streamlit as st

from dashboard.components import patrones
from dashboard.components import temas as temas_component
from dashboard.components.filters import render_trends_period_filter
from dashboard.layout import render_page_header
from dashboard.supabase_queries import (
    format_relative_iso,
    get_temas_recurrentes,
    list_temas_recurrentes_snapshots,
)


def _resolve_temas_query(mode: str, days: int | None) -> dict | None:
    if mode == "all":
        snapshots = list_temas_recurrentes_snapshots()
        if not snapshots:
            return None
        labels = {
            row["id"]: (
                f"{format_relative_iso(row.get('created_at'))} · "
                f"{row.get('periodo_dias', '?')} días"
            )
            for row in snapshots
        }
        snapshot_id = st.selectbox(
            "Análisis guardado",
            options=list(labels.keys()),
            format_func=lambda sid: labels[sid],
            key="temas_snapshot_pick",
        )
        return get_temas_recurrentes(snapshot_id=int(snapshot_id))

    if mode == "days" and days is not None:
        return get_temas_recurrentes(periodo_dias=days)

    return get_temas_recurrentes()


def _render_temas_tab() -> None:
    st.caption(
        "Categorías que más repite el clasificador en el período, "
        "con conteos y tendencia."
    )

    col_period, col_refresh = st.columns([3, 1])
    with col_period:
        mode, days = render_trends_period_filter(key_prefix="temas")
    with col_refresh:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", key="temas_refresh"):
            get_temas_recurrentes.clear()
            list_temas_recurrentes_snapshots.clear()
            st.rerun()

    st.caption(
        "El worker actualiza este análisis automáticamente cada día. "
        "Elegí el período o un análisis del historial."
    )
    st.divider()

    try:
        data = _resolve_temas_query(mode, days)
    except Exception as exc:
        st.error(f"Error al cargar temas recurrentes: {exc}")
        return

    if data is None and mode == "days" and days is not None:
        st.warning(
            f"No hay análisis guardado para **{days} días**. "
            "Probá «Último análisis», «Todo el historial» o ejecutá el job manual."
        )
        return

    temas_component.render(data)


def render() -> None:
    render_page_header("tendencias")

    tab_temas, tab_patrones = st.tabs(["Temas", "Patrones"])

    with tab_temas:
        _render_temas_tab()

    with tab_patrones:
        patrones.render()
