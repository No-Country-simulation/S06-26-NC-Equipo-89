"""
Componente: Urgencia — distribución y mensajes por nivel (Alta, Media, Baja).
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from dashboard.components.feedback_card import feedback_card_html
from dashboard.components.formatters import format_fecha
from dashboard.components.ui import empty_state, section_header
from dashboard.supabase_queries import get_mensajes_por_urgencia, get_urgencia_distribucion
from dashboard.theme import ALTAIR_THEME, IMPACT_BADGES

alt.theme.enable("default")
alt.themes.register("fc_urg_theme", lambda: ALTAIR_THEME)
alt.theme.enable("fc_urg_theme")

_URG_COLORS = {
    "Alta": IMPACT_BADGES["Alta"][1],
    "Media": IMPACT_BADGES["Media"][1],
    "Baja": IMPACT_BADGES["Baja"][1],
}


def render() -> None:
    section_header(
        "Urgencia del feedback",
        "Distribución por nivel y mensajes que requieren seguimiento.",
    )

    try:
        distrib = get_urgencia_distribucion()
    except Exception as e:
        st.error(f"Error cargando distribución: {e}")
        return

    df_dist = pd.DataFrame(distrib)
    total = df_dist["cantidad"].sum() or 1

    c1, c2, c3, c4 = st.columns(4)
    counts = {r["urgencia"]: r["cantidad"] for r in distrib}
    c1.metric("Alta", counts.get("Alta", 0))
    c2.metric("Media", counts.get("Media", 0))
    c3.metric("Baja", counts.get("Baja", 0))
    c4.metric("Total", total)

    if df_dist["cantidad"].sum() > 0:
        chart = (
            alt.Chart(df_dist)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("cantidad:Q", title="Mensajes"),
                y=alt.Y("urgencia:N", sort=["Alta", "Media", "Baja"], title="Urgencia"),
                color=alt.Color(
                    "urgencia:N",
                    scale=alt.Scale(
                        domain=list(_URG_COLORS.keys()),
                        range=[IMPACT_BADGES[k][1] for k in _URG_COLORS],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("urgencia:N", title="Urgencia"),
                    alt.Tooltip("cantidad:Q", title="Cantidad"),
                ],
            )
            .properties(height=180)
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    nivel = st.radio(
        "Ver mensajes con urgencia",
        options=["Alta", "Media", "Baja", "Todos"],
        horizontal=True,
        key="urgencia_nivel",
    )

    urgencia_filtro = None if nivel == "Todos" else nivel

    try:
        rows = get_mensajes_por_urgencia(urgencia=urgencia_filtro, limit=50)
    except Exception as e:
        st.error(f"Error cargando mensajes: {e}")
        return

    if not rows:
        empty_state(f"No hay mensajes con urgencia {nivel.lower()}.")
        return

    if nivel == "Alta":
        st.warning("Estos mensajes requieren atención prioritaria del equipo de CS.")

    for row in rows:
        cats = row.get("categorias", [])
        if not isinstance(cats, list):
            cats = [cats] if cats else []
        st.markdown(
            feedback_card_html(
                external_id=str(row.get("external_id", "")),
                fuente=str(row.get("fuente", "")),
                sentimiento=str(row.get("sentimiento", "")),
                urgencia=str(row.get("urgencia", "")),
                confianza=row.get("confianza"),
                idioma=str(row.get("idioma", "")),
                resumen=str(row.get("resumen", "")),
                texto=str(row.get("texto", "")),
                categorias=cats,
                fecha=format_fecha(row.get("timestamp") or row.get("clasificado_at", "")),
            ),
            unsafe_allow_html=True,
        )

    st.caption(f"{len(rows)} mensaje(s) mostrados.")
