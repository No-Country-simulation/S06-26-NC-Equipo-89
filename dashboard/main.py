"""
Dashboard Operativo — Feedback Classifier
Orquestador principal de la interfaz de Streamlit.
Conexión directa a Supabase (ADR-007), sin pasar por FastAPI.
"""
import streamlit as st

# ── Configuración general de la página ────────────────────────────────────────
st.set_page_config(
    page_title="Feedback Classifier | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Importar componentes DESPUÉS de set_page_config ───────────────────────────
from dashboard.components import metricas, sentimiento, urgencia, patrones, copilot

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
        }
        [data-testid="stMetricLabel"] { font-size: 0.82rem; color: #64748b; }
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
        .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/No-Country-simulation/S06-26-NC-Equipo-89/main/README.md",
        width=60,
        use_container_width=False,
    )
    st.markdown("## 📊 Feedback Classifier")
    st.markdown("Dashboard operativo de Customer Success")
    st.divider()

    seccion = st.radio(
        "Navegar a:",
        options=[
            "🏠 Vista General",
            "💬 Sentimiento y Categorías",
            "🚨 Alertas de Urgencia",
            "🔍 Patrones Detectados",
            "🤖 Copilot",
        ],
        index=0,
        key="nav_seccion",
    )

    st.divider()
    if st.button("🔄 Refrescar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Los datos se actualizan automáticamente cada 60 segundos.")

# ── Encabezado principal ───────────────────────────────────────────────────────
st.markdown("# 📊 Dashboard Operativo — Feedback Classifier")
st.divider()

# ── Renderizar sección activa ──────────────────────────────────────────────────
if seccion == "🏠 Vista General":
    metricas.render()
    st.markdown("---")
    sentimiento.render()

elif seccion == "💬 Sentimiento y Categorías":
    sentimiento.render()

elif seccion == "🚨 Alertas de Urgencia":
    urgencia.render()

elif seccion == "🔍 Patrones Detectados":
    patrones.render()

elif seccion == "🤖 Copilot":
    copilot.render()
