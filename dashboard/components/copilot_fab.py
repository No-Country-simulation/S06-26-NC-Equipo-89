"""Copilot — lanzador sidebar + ventana modal (st.dialog)."""

import streamlit as st

from dashboard.components.copilot import render_chat


def render_sidebar_button() -> None:
    """CTA fijo en el sidebar."""
    if st.button(
        "Copilot — Asistente IA",
        type="primary",
        width="stretch",
        key="copilot_launch_sidebar",
    ):
        st.session_state.copilot_dialog_open = True
        st.session_state.copilot_seen = True
        st.rerun()


@st.dialog("Copilot — Asistente de Feedback", width="large")
def _copilot_dialog() -> None:
    head_col, close_col = st.columns([6, 1])
    with head_col:
        st.markdown(
            """
            <div class="fc-copilot-dialog-hero">
                <p class="fc-copilot-dialog-title">Preguntá sobre tu feedback</p>
                <p class="fc-copilot-dialog-sub">
                    Respuestas basadas en feedback real indexado.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with close_col:
        if st.button("✕", key="copilot_close_x", help="Cerrar"):
            st.session_state.copilot_dialog_open = False
            st.rerun()

    render_chat(compact=True)

    foot_col, clear_col = st.columns([3, 1])
    with clear_col:
        if st.button("Limpiar conversación", width="stretch", type="secondary"):
            st.session_state.copilot_messages = []
            st.rerun()


def open_dialog_if_needed() -> None:
    """Abre el modal si el usuario lo solicitó."""
    if st.session_state.get("copilot_dialog_open"):
        _copilot_dialog()
