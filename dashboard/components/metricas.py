"""
Componente: KPIs de alto nivel.
Muestra 4 tarjetas de métricas en la parte superior del dashboard.
"""
import streamlit as st
from dashboard.supabase_queries import get_kpis, get_ultimo_lote_metricas


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

    try:
        ultimo = get_ultimo_lote_metricas()
    except Exception:
        ultimo = None

    if ultimo and ultimo.get("datos"):
        datos = ultimo["datos"]
        st.markdown("---")
        st.markdown("**Último lote procesado**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Mensajes en lote", datos.get("total_procesados", 0))
        with c2:
            sent = datos.get("sentimientos", {})
            st.caption(
                f"Positivo: {sent.get('Positivo', 0)} · "
                f"Negativo: {sent.get('Negativo', 0)} · "
                f"Neutral: {sent.get('Neutral', 0)}"
            )
        with c3:
            urg = datos.get("urgencias", {})
            st.caption(
                f"Urgencia Alta: {urg.get('Alta', 0)} · "
                f"Media: {urg.get('Media', 0)} · "
                f"Baja: {urg.get('Baja', 0)}"
            )
        if datos.get("categorias_top"):
            st.caption(
                "Top categorías: "
                + ", ".join(f"{k} ({v})" for k, v in datos["categorias_top"].items())
            )
