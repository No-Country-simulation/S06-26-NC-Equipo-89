"""Shell compartido — sidebar, encabezado y banners."""

from __future__ import annotations

import streamlit as st

from dashboard.components import copilot_fab, health_banner, status_bar
from dashboard.components.pipeline_status import render as render_pipeline_sidebar
from dashboard.components.ui import brand_sidebar, inject_styles, page_header
from dashboard.theme import ASSETS_DIR, PAGE_TITLES


def init_session() -> None:
    """Estado de sesión global del dashboard."""
    if "copilot_dialog_open" not in st.session_state:
        st.session_state.copilot_dialog_open = False
    if "fc_auto_refresh" not in st.session_state:
        st.session_state.fc_auto_refresh = True


def render_sidebar() -> None:
    """Sidebar completo — debe llamarse ANTES de st.navigation()."""
    with st.sidebar:
        brand_sidebar(
            ASSETS_DIR / "logo.svg",
            "Feedback Classifier",
            "Monitoreo de feedback en tiempo casi real",
        )
        st.divider()
        copilot_fab.render_sidebar_button()
        render_pipeline_sidebar(compact=True)

        st.divider()
        if st.button("Refrescar datos", width="stretch", type="secondary"):
            st.cache_data.clear()
            st.rerun()

        st.toggle(
            "Auto-actualizar cada 30 s",
            key="fc_auto_refresh",
            help="Actualiza cola y última actividad sin recargar la página",
        )

        st.caption("Los KPIs y gráficos se refrescan con «Refrescar datos».")

        st.divider()


def render_page_header(seccion_id: str, *, show_health: bool = True) -> None:
    """Título, subtítulo, status bar y health banner."""
    title, subtitle = PAGE_TITLES[seccion_id]
    page_header(title, subtitle)
    status_bar.render()
    if show_health:
        health_banner.render(show_fastapi=seccion_id in ("general", "carga", "exportar"))
    st.divider()


def setup() -> None:
    """Configuración inicial de página."""
    init_session()
    inject_styles()
