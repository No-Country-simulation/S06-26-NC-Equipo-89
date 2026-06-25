"""Estado visual del pipeline de procesamiento (cola worker)."""

from __future__ import annotations

import streamlit as st

from dashboard.supabase_queries import get_queue_health


def _chip(label: str, value: int, css_class: str) -> str:
    if value <= 0:
        return ""
    return f'<span class="fc-chip {css_class}">{label}: {value}</span>'


def render(*, compact: bool = False) -> None:
    """Muestra chips de pendiente / procesando / error."""
    try:
        health = get_queue_health()
    except Exception:
        return

    pending = health.get("pendientes", 0)
    processing = health.get("procesando", 0)
    errors = health.get("errores", 0)

    if pending == processing == errors == 0:
        if not compact:
            st.markdown(
                '<span class="fc-chip fc-chip-ok">Cola al día</span>',
                unsafe_allow_html=True,
            )
        return

    chips = "".join(
        c
        for c in (
            _chip("Pendientes", pending, "fc-chip-pending"),
            _chip("Procesando", processing, "fc-chip-processing"),
            _chip("Errores", errors, "fc-chip-error"),
        )
        if c
    )
    if chips:
        st.markdown(f'<div class="fc-pipeline">{chips}</div>', unsafe_allow_html=True)
