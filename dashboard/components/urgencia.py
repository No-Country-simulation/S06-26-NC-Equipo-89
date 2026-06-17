"""
Componente: Tabla de Alertas de Urgencia Alta.
Muestra los últimos 20 mensajes clasificados con urgencia = 'Alta'.
"""
import streamlit as st
import pandas as pd
from dashboard.supabase_queries import get_alertas_urgencia_alta


def render():
    st.subheader("🚨 Alertas de Urgencia Alta")
    st.caption("Mensajes que requieren atención inmediata del equipo de Customer Success.")

    try:
        rows = get_alertas_urgencia_alta(limit=20)

        if not rows:
            st.success("✅ No hay mensajes de urgencia alta en este momento.")
            return

        df = pd.DataFrame(rows)

        # Renombrar columnas para mejor legibilidad
        df = df.rename(columns={
            "fuente":       "Fuente",
            "texto":        "Mensaje del Cliente",
            "categorias":   "Categorías",
            "timestamp":    "Fecha/Hora",
            "external_id":  "ID",
        })

        # Formatear la fecha a algo legible
        if "Fecha/Hora" in df.columns:
            df["Fecha/Hora"] = pd.to_datetime(df["Fecha/Hora"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(
            df[["Fuente", "Mensaje del Cliente", "Categorías", "Fecha/Hora"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mensaje del Cliente": st.column_config.TextColumn(
                    width="large",
                    help="Texto original del cliente"
                ),
                "Categorías": st.column_config.TextColumn(width="medium"),
                "Fuente": st.column_config.TextColumn(width="small"),
                "Fecha/Hora": st.column_config.TextColumn(width="small"),
            }
        )

        st.caption(f"Mostrando {len(df)} de los últimos registros más recientes.")

    except Exception as e:
        st.error(f"Error cargando alertas: {e}")
