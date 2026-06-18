"""Shell compartido — sidebar, encabezado y banners."""

from __future__ import annotations

import streamlit as st

from dashboard.components import copilot_fab, health_banner, status_bar
from dashboard.components.ui import brand_sidebar, inject_styles, page_header
from dashboard.theme import ASSETS_DIR, PAGE_TITLES

_THEME_KEY = "fc_dark_mode"


def init_session() -> None:
    """Estado de sesión global del dashboard."""
    if "copilot_dialog_open" not in st.session_state:
        st.session_state.copilot_dialog_open = False
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if _THEME_KEY not in st.session_state:
        st.session_state[_THEME_KEY] = st.session_state.theme == "dark"


def _on_theme_toggle() -> None:
    st.session_state.theme = "dark" if st.session_state[_THEME_KEY] else "light"
    st.session_state.copilot_dialog_open = False


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

        st.divider()
        if st.button("Refrescar datos", use_container_width=True, type="secondary"):
            st.cache_data.clear()
            st.rerun()

        st.caption("Los datos se actualizan automáticamente cada 60 segundos.")

        st.divider()
        st.toggle(
            "Modo oscuro",
            key=_THEME_KEY,
            on_change=_on_theme_toggle,
        )
        st.session_state.theme = "dark" if st.session_state[_THEME_KEY] else "light"


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
