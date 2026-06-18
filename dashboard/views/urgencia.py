"""Página — Alertas de Urgencia."""

from dashboard.components import urgencia
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("urgencia")
    urgencia.render()
