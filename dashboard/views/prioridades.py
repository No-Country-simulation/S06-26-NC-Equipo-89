"""Vista compuesta — Urgencia y acciones sugeridas."""

import streamlit as st

from dashboard.components import acciones, urgencia
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("prioridades")

    tab_urgentes, tab_acciones = st.tabs(["Urgentes", "Señales del agente"])

    with tab_urgentes:
        urgencia.render()

    with tab_acciones:
        acciones.render()
