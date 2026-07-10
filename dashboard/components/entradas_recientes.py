"""Entradas recientes — confirma si la ingesta (n8n / carga) llegó a Supabase."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.ui import empty_state, section_header, source_badge
from dashboard.supabase_queries import format_relative_iso, get_entradas_recientes

_ESTADO_CHIP: dict[str, tuple[str, str]] = {
    "pendiente": ("En cola", "fc-chip-pending"),
    "procesando": ("Procesando", "fc-chip-processing"),
    "procesado": ("Clasificado", "fc-chip-ok"),
    "error": ("Error", "fc-chip-error"),
}


def _estado_chip(estado: str) -> str:
    label, css = _ESTADO_CHIP.get(estado or "", (estado or "—", "fc-chip-pending"))
    return f'<span class="fc-chip {css}">{html.escape(label)}</span>'


def _preview_text(texto: str, max_len: int = 90) -> str:
    clean = " ".join((texto or "").split())
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 1].rstrip() + "…"


def _row_html(item: dict) -> str:
    fuente = source_badge(item.get("fuente") or "")
    estado = _estado_chip(item.get("estado") or "")
    cuando = html.escape(format_relative_iso(item.get("created_at") or ""))
    texto = html.escape(_preview_text(item.get("texto") or ""))
    return (
        f'<div class="fc-entrada-row">'
        f'<div class="fc-entrada-meta">{fuente}{estado}'
        f'<span class="fc-entrada-when">{cuando}</span></div>'
        f'<p class="fc-entrada-text">{texto or "—"}</p>'
        f"</div>"
    )


def _render_list() -> None:
    section_header(
        "Entradas recientes",
        "Confirmá si WhatsApp, Tally, Forms o la carga manual llegaron a Supabase.",
    )
    try:
        rows = get_entradas_recientes(10)
    except EnvironmentError:
        st.caption("Supabase no configurado — no se pueden listar entradas.")
        return
    except Exception as exc:
        st.error(f"No se pudieron cargar las entradas recientes: {exc}")
        return

    if not rows:
        empty_state(
            "Aún no hay mensajes en cola. Enviá algo desde n8n o cargá un archivo."
        )
        return

    body = "".join(_row_html(item) for item in rows)
    st.markdown(f'<div class="fc-entradas">{body}</div>', unsafe_allow_html=True)
    st.caption(
        "Se actualiza cada 30 s con el auto-refresh. "
        "«En cola» = llegó · «Clasificado» = el worker ya lo procesó."
    )


@st.fragment(run_every=30)
def _live_fragment() -> None:
    get_entradas_recientes.clear()
    _render_list()


def render() -> None:
    """Lista corta de las últimas ingestas; auto-refresh si está activo."""
    if st.session_state.get("fc_auto_refresh", True):
        _live_fragment()
    else:
        _render_list()
