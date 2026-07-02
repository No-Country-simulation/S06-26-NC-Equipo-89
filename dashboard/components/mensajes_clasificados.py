"""
Componente: Bandeja de mensajes clasificados.
Muestra resumen, confianza, idioma y categorías (campos que antes solo estaban en export).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.formatters import format_fecha
from dashboard.components.feedback_card import feedback_card_html
from dashboard.components.filters import filter_dataframe_by_date, resolve_display_limit
from dashboard.components.ui import empty_state, section_header
from dashboard.supabase_queries import get_clasificados_export


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_dataframe_by_date(df, key_prefix="msg")

    fuentes = sorted(filtered["fuente"].dropna().unique().tolist())
    if fuentes:
        sel = st.multiselect("Fuente", fuentes, default=fuentes, key="msg_fuente")
        if sel:
            filtered = filtered[filtered["fuente"].isin(sel)]

    sentimientos = sorted(filtered["sentimiento"].dropna().unique().tolist())
    if sentimientos:
        sel = st.multiselect("Sentimiento", sentimientos, default=sentimientos, key="msg_sent")
        if sel:
            filtered = filtered[filtered["sentimiento"].isin(sel)]

    urgencias = sorted(filtered["urgencia"].dropna().unique().tolist())
    if urgencias:
        sel = st.multiselect("Urgencia", urgencias, default=urgencias, key="msg_urg")
        if sel:
            filtered = filtered[filtered["urgencia"].isin(sel)]

    idiomas = sorted(filtered["idioma"].dropna().unique().tolist())
    if idiomas:
        sel = st.multiselect("Idioma", idiomas, default=idiomas, key="msg_idioma")
        if sel:
            filtered = filtered[filtered["idioma"].isin(sel)]

    if st.checkbox("Solo baja confianza (< 70%)", key="msg_low_conf"):
        filtered = filtered[filtered["confianza"].fillna(0) < 0.7]

    buscar = st.text_input("Buscar en texto o resumen", key="msg_search", placeholder="ej. precio, app...")
    if buscar.strip():
        q = buscar.strip().lower()
        mask = (
            filtered["texto"].fillna("").str.lower().str.contains(q, regex=False)
            | filtered["resumen"].fillna("").str.lower().str.contains(q, regex=False)
        )
        filtered = filtered[mask]

    return filtered


def render() -> None:
    section_header(
        "Bandeja de clasificados",
        "Cada tarjeta muestra lo que el agente extrajo: resumen, confianza, idioma y categorías.",
    )

    try:
        rows = get_clasificados_export()
    except EnvironmentError as e:
        st.error(f"Error de configuración: {e}")
        return
    except Exception as e:
        st.error(f"No se pudieron cargar los mensajes: {e}")
        return

    if not rows:
        empty_state("Aún no hay feedback clasificado.")
        return

    df = pd.DataFrame(rows)
    low_conf = int((df["confianza"].fillna(0) < 0.7).sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total clasificados", len(df))
    m2.metric("Urgencia alta", int((df["urgencia"] == "Alta").sum()))
    m3.metric("Sentimiento negativo", int((df["sentimiento"] == "Negativo").sum()))
    m4.metric("Revisar (conf. < 70%)", low_conf, help="Clasificaciones que conviene validar manualmente")

    st.markdown("---")
    with st.expander("Filtros", expanded=True):
        filtered = _apply_filters(df)

    limit = resolve_display_limit(len(filtered), key_prefix="msg")
    st.caption(f"Mostrando {min(len(filtered), limit)} de {len(filtered)} (total en base {len(df)})")

    if filtered.empty:
        empty_state("Ningún mensaje coincide con los filtros.")
        return

    page_slice = filtered.head(limit)
    for _, row in page_slice.iterrows():
        cats = row.get("categorias", [])
        if not isinstance(cats, list):
            cats = [cats] if cats else []
        fecha = format_fecha(row.get("clasificado_at") or row.get("timestamp", ""))
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
                fecha=fecha,
            ),
            unsafe_allow_html=True,
        )

    if len(filtered) > limit:
        st.info(
            f"Hay {len(filtered) - limit} mensajes más. Activá «Mostrar todos» "
            "o ampliá «Mensajes a mostrar»."
        )
