"""Página — Mensajes clasificados (detalle del agente)."""

from dashboard.components import mensajes_clasificados
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("mensajes")
    mensajes_clasificados.render()
