"""Página — Exportar Datos."""

from dashboard.components import exportar
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("exportar")
    exportar.render()
