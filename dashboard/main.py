"""
Dashboard Operativo — Feedback Classifier v3
Entry point multipágina con st.navigation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboard.components import copilot_fab
from dashboard.layout import render_sidebar, setup
from dashboard.views import acciones, carga, exportar, general, mensajes, patrones, revision, sentimiento, temas, urgencia
from dashboard.theme import ASSETS_DIR, NAV_GROUPS

st.set_page_config(
    page_title="Feedback Classifier",
    page_icon=str(ASSETS_DIR / "logo.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

setup()
render_sidebar()

# ── Navegación multipágina agrupada ───────────────────────────────────────────
_PAGE_MODULES = {
    "general": general,
    "acciones": acciones,
    "revision": revision,
    "sentimiento": sentimiento,
    "urgencia": urgencia,
    "mensajes": mensajes,
    "patrones": patrones,
    "temas": temas,
    "exportar": exportar,
    "carga": carga,
}

nav_pages: dict[str, list[st.Page]] = {}
for group_name, items in NAV_GROUPS.items():
    nav_pages[group_name] = [
        st.Page(
            _PAGE_MODULES[item["id"]].render,
            title=item["label"],
            icon=item["icon"],
            url_path=item["url_path"],
        )
        for item in items
    ]

pg = st.navigation(nav_pages, position="sidebar")
pg.run()

# ── Modal Copilot (global) ────────────────────────────────────────────────────
copilot_fab.open_dialog_if_needed()
