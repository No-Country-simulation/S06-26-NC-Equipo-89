"""
Componente: KPIs de alto nivel.
Muestra 4 tarjetas de métricas en la parte superior del dashboard.
"""
import streamlit as st
from dashboard.supabase_queries import get_kpis


def render():
    st.subheader("📊 Vista General")

    try:
        kpis = get_kpis()
    except EnvironmentError as e:
        st.error(f"Error de configuración: {e}")
        return
    except Exception as e:
        st.error(f"No se pudieron cargar las métricas: {e}")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="✅ Mensajes Procesados",
            value=f"{kpis['total_procesados']:,}",
        )

    with col2:
        st.metric(
            label="😠 Sentimiento Negativo",
            value=f"{kpis['pct_negativos']}%",
            delta=None,
            help="Porcentaje de mensajes clasificados como Negativos sobre el total."
        )

    with col3:
        st.metric(
            label="🚨 Alertas Urgencia Alta",
            value=f"{kpis['alertas_altas']:,}",
        )

    with col4:
        st.metric(
            label="🔍 Patrones Detectados",
            value=f"{kpis['total_patrones']:,}",
        )
