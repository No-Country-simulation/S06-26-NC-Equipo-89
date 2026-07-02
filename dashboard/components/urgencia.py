"""
Componente: Urgencia — distribución y mensajes por nivel (Alta, Media, Baja).
Vista de monitoreo: muestra cómo el agente clasificó la urgencia, sin workflow de atención.
"""
from __future__ import annotations

from collections import Counter

import altair as alt
import pandas as pd
import streamlit as st

from dashboard.components.feedback_card import feedback_card_html
from dashboard.components.filters import filter_dataframe_by_date, resolve_display_limit
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

_URGENCIA_CRITERIA = {
    "Alta": "cancelación, furia, riesgo legal o caída del sistema",
    "Media": "queja, problema menor o sugerencia",
    "Baja": "duda, halago o mensaje neutral",
}


def _pct(part: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{part / total * 100:.0f}%"


def _render_criterio_info(nivel: str) -> None:
    if nivel == "Todos":
        st.caption(
            "La urgencia la asigna el agente al clasificar cada mensaje "
            "(Alta / Media / Baja según tono e impacto del feedback)."
        )
        return
    criterio = _URGENCIA_CRITERIA.get(nivel, "")
    st.caption(
        f"**Urgencia {nivel}** — criterio del clasificador: {criterio}."
    )


def _render_insights(rows: list[dict], nivel: str) -> None:
    """Resumen agregado del recorte actual (solo datos del agente)."""
    if not rows:
        return

    sent_counts = Counter(r.get("sentimiento") or "—" for r in rows)
    cat_counts: Counter[str] = Counter()
    fuente_counts: Counter[str] = Counter()
    for row in rows:
        fuente_counts[row.get("fuente") or "—"] += 1
        cats = row.get("categorias") or []
        if not isinstance(cats, list):
            cats = [cats] if cats else []
        for cat in cats:
            if cat:
                cat_counts[cat] += 1

    top_cats = ", ".join(f"**{name}** ({n})" for name, n in cat_counts.most_common(3))
    sent_line = " · ".join(f"{s}: {n}" for s, n in sent_counts.most_common())
    fuente_line = " · ".join(f"{f}: {n}" for f, n in fuente_counts.most_common(3))

    label = f"urgencia {nivel}" if nivel != "Todos" else "todos los niveles"
    st.markdown(
        f"En este recorte ({label}, {len(rows)} mensaje(s)): "
        f"sentimiento {sent_line}."
        + (f" Categorías más frecuentes: {top_cats}." if top_cats else "")
        + (f" Fuentes: {fuente_line}." if fuente_line else "")
    )


def render() -> None:
    section_header(
        "Clasificación por urgencia",
        "Distribución y detalle de cómo el agente etiquetó cada mensaje.",
    )

    try:
        distrib = get_urgencia_distribucion()
    except Exception as e:
        st.error(f"Error cargando distribución: {e}")
        return

    df_dist = pd.DataFrame(distrib)
    total = int(df_dist["cantidad"].sum() or 0)

    counts = {r["urgencia"]: int(r["cantidad"]) for r in distrib}
    alta = counts.get("Alta", 0)
    media = counts.get("Media", 0)
    baja = counts.get("Baja", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alta", alta, delta=_pct(alta, total), delta_color="off")
    c2.metric("Media", media, delta=_pct(media, total), delta_color="off")
    c3.metric("Baja", baja, delta=_pct(baja, total), delta_color="off")
    c4.metric("Total clasificados", total)

    if total > 0:
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
        st.altair_chart(chart, width="stretch")

    st.markdown("---")
    nivel = st.radio(
        "Nivel de urgencia",
        options=["Alta", "Media", "Baja", "Todos"],
        horizontal=True,
        key="urgencia_nivel",
    )
    _render_criterio_info(nivel)

    urgencia_filtro = None if nivel == "Todos" else nivel

    try:
        rows = get_mensajes_por_urgencia(urgencia=urgencia_filtro, limit=2000)
    except Exception as e:
        st.error(f"Error cargando mensajes: {e}")
        return

    if not rows:
        empty_state(f"Ningún mensaje clasificado con urgencia {nivel.lower()}.")
        return

    df = pd.DataFrame(rows)
    with st.expander("Filtros", expanded=True):
        df = filter_dataframe_by_date(df, key_prefix="urg")

    filtered_count = len(df)
    if filtered_count == 0:
        empty_state("Ningún mensaje en el rango de fechas seleccionado.")
        return

    limit = resolve_display_limit(filtered_count, key_prefix="urg")
    rows_filtered = df.head(limit).to_dict("records")

    _render_insights(rows_filtered, nivel)
    st.markdown("---")

    for row in rows_filtered:
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

    st.caption(
        f"Mostrando {len(rows_filtered)} de {filtered_count} mensaje(s) filtrados · "
        "ordenados por fecha de clasificación (más recientes primero)."
    )
    if filtered_count > limit:
        st.info(
            f"Hay {filtered_count - limit} mensajes más. Activá «Mostrar todos» "
            "o ampliá «Mensajes a mostrar»."
        )
