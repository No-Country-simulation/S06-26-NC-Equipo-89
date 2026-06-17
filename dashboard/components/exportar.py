"""
Componente: Exportación de datos clasificados (ADR-007).
Permite descargar feedback_clasificado en CSV o JSON.
"""
import json

import pandas as pd
import streamlit as st

from dashboard.supabase_queries import get_clasificados_export


def render() -> None:
    st.subheader("Exportar datos clasificados")
    st.caption("Descarga el feedback ya procesado por el agente LangGraph.")

    try:
        rows = get_clasificados_export()
    except EnvironmentError as e:
        st.error(f"Error de configuración: {e}")
        return
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
        return

    if not rows:
        st.info("No hay registros clasificados para exportar.")
        return

    st.metric("Registros disponibles", len(rows))

    df = pd.DataFrame(rows)
    csv_data = df.to_csv(index=False).encode("utf-8")
    json_data = json.dumps(rows, ensure_ascii=False, indent=2, default=str).encode("utf-8")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Descargar CSV",
            data=csv_data,
            file_name="feedback_clasificado.csv",
            mime="text/csv",
            type="primary",
        )
    with col2:
        st.download_button(
            label="Descargar JSON",
            data=json_data,
            file_name="feedback_clasificado.json",
            mime="application/json",
        )

    with st.expander("Vista previa (10 filas)"):
        st.dataframe(df.head(10), use_container_width=True)
