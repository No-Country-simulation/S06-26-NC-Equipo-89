"""
Componente: Patrones detectados por el Agente LangGraph.
Muestra cards con descripción, frecuencia e impacto, filtrables.
"""
import streamlit as st

from dashboard.components.filters import render_trends_period_filter
from dashboard.components.ui import badge, empty_state, pattern_card, section_header
from dashboard.supabase_queries import get_patrones
from dashboard.theme import FREQ_ORDER, IMPACT_BADGES, IMPACT_ORDER


def _impact_badge(label: str, value: str) -> str:
    _name, bg, color = IMPACT_BADGES.get(value, ("", "#f1f5f9", "#475569"))
    return badge(f"{label}: {value}", bg, color)


def _sort_key(patron: dict) -> tuple[int, int]:
    impacto = patron.get("impacto", "Bajo")
    frecuencia = patron.get("frecuencia", "Baja")
    return (IMPACT_ORDER.get(impacto, 99), FREQ_ORDER.get(frecuencia, 99))


def _resolve_patrones_query(
    mode: str,
    days: int | None,
    impacto_filtro: str,
) -> list[dict]:
    if mode == "latest":
        return get_patrones(impacto_filtro, latest_tick_only=True)
    if mode == "days" and days is not None:
        return get_patrones(
            impacto_filtro,
            latest_tick_only=False,
            since_days=days,
        )
    return get_patrones(impacto_filtro, latest_tick_only=False)


def render():
    section_header(
        "Patrones detectados",
        "Insights de negocio extraídos automáticamente por el pipeline de IA.",
    )

    col_period, col_impact = st.columns(2)
    with col_period:
        mode, days = render_trends_period_filter(key_prefix="patrones")
    with col_impact:
        filtro = st.selectbox(
            "Filtrar por impacto",
            options=["Todos", "Alto", "Medio", "Bajo"],
            index=0,
            key="filtro_impacto",
        )

    try:
        patrones_list = _resolve_patrones_query(mode, days, filtro)

        if not patrones_list:
            empty_state(
                "Sin patrones en el período seleccionado. Cargá feedback de prueba desde "
                "**Carga de datos** o probá «Todo el historial»."
            )
            return

        patrones_sorted = sorted(patrones_list, key=_sort_key)

        for patron in patrones_sorted:
            descripcion = patron.get("descripcion", "Sin descripción")
            frecuencia = patron.get("frecuencia", "Desconocida")
            impacto = patron.get("impacto", "Desconocido")

            badges_html = _impact_badge("Frecuencia", frecuencia) + _impact_badge(
                "Impacto", impacto
            )
            pattern_card(descripcion, badges_html)

        scope = "último análisis" if mode == "latest" else (
            f"últimos {days} días" if mode == "days" else "todo el historial"
        )
        st.caption(f"{len(patrones_sorted)} patrón(es) · {scope}")

    except Exception as e:
        st.error(f"Error cargando patrones: {e}")
