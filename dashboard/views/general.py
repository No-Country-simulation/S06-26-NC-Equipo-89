"""Páginas del dashboard — Vista General."""

import streamlit as st

from dashboard.components import alertas, metricas, pipeline_status, sentimiento
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("general")

    if not st.session_state.get("copilot_seen"):
        st.info(
            "💡 **Tip:** Usá **Copilot — Asistente IA** en el menú lateral "
            "para preguntar sobre tu feedback en lenguaje natural."
        )
        if st.button("Entendido", key="dismiss_copilot_onboarding"):
            st.session_state.copilot_seen = True
            st.rerun()

    metricas.render()
    alertas.render()
    pipeline_status.render()
    st.markdown("---")
    sentimiento.render()
