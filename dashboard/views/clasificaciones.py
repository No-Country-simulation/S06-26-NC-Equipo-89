"""Vista compuesta — Mensajes clasificados y revisión humana."""

import streamlit as st

from dashboard.components import mensajes_clasificados, revision
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("clasificaciones")

    tab_mensajes, tab_revision = st.tabs(["Mensajes", "Revisar"])

    with tab_mensajes:
        mensajes_clasificados.render()

    with tab_revision:
        revision.render()
