"""
Componente: Exportación de datos clasificados (ADR-007).
Permite descargar feedback_clasificado en CSV o JSON con filtros.
"""
import json
from datetime import datetime

import pandas as pd
import streamlit as st

from dashboard.components.ui import empty_state, section_header
from dashboard.supabase_queries import get_clasificados_export


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros de fecha, fuente y sentimiento."""
    filtered = df.copy()

    if "clasificado_at" in filtered.columns:
        filtered["clasificado_at"] = pd.to_datetime(filtered["clasificado_at"], errors="coerce")
        date_col = filtered["clasificado_at"]
    elif "timestamp" in filtered.columns:
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"], errors="coerce")
        date_col = filtered["timestamp"]
    else:
        date_col = None

    if date_col is not None:
        min_d = date_col.min()
        max_d = date_col.max()
        if pd.notna(min_d) and pd.notna(max_d):
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_d.date(), max_d.date()),
                key="export_date_range",
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = date_range
                mask = (date_col.dt.date >= start) & (date_col.dt.date <= end)
                filtered = filtered[mask]

    fuentes = sorted(filtered["fuente"].dropna().unique().tolist()) if "fuente" in filtered.columns else []
    if fuentes:
        sel_fuentes = st.multiselect("Fuente", options=fuentes, default=fuentes, key="export_fuente")
        if sel_fuentes:
            filtered = filtered[filtered["fuente"].isin(sel_fuentes)]

    sentimientos = (
        sorted(filtered["sentimiento"].dropna().unique().tolist())
        if "sentimiento" in filtered.columns
        else []
    )
    if sentimientos:
        sel_sent = st.multiselect(
            "Sentimiento", options=sentimientos, default=sentimientos, key="export_sent"
        )
        if sel_sent:
            filtered = filtered[filtered["sentimiento"].isin(sel_sent)]

    return filtered


def render() -> None:
    section_header(
        "Exportar datos",
        "Descarga el feedback ya procesado por el agente LangGraph.",
    )

    try:
        rows = get_clasificados_export()
    except EnvironmentError as e:
        st.error(f"Error de configuración: {e}")
        return
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
        return

    if not rows:
        empty_state("No hay registros clasificados para exportar.")
        return

    df = pd.DataFrame(rows)
    filtered = _apply_filters(df)

    st.metric("Registros a exportar", len(filtered), delta=f"de {len(df)} totales")

    if filtered.empty:
        st.warning("Ningún registro coincide con los filtros seleccionados.")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv_name = f"feedback_clasificado_{ts}.csv"
    json_name = f"feedback_clasificado_{ts}.json"

    csv_data = filtered.to_csv(index=False).encode("utf-8")
    json_data = json.dumps(
        filtered.to_dict(orient="records"), ensure_ascii=False, indent=2, default=str
    ).encode("utf-8")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"Descargar CSV ({len(filtered)} filas)",
            data=csv_data,
            file_name=csv_name,
            mime="text/csv",
            type="primary",
        )
    with col2:
        st.download_button(
            label=f"Descargar JSON ({len(filtered)} filas)",
            data=json_data,
            file_name=json_name,
            mime="application/json",
        )

    with st.expander("Vista previa (10 filas)"):
        st.dataframe(filtered.head(10), use_container_width=True)

    st.caption("Descarga lista — el archivo incluye solo los registros filtrados.")
