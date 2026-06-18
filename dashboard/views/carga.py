"""Página — Carga de datos."""

from dashboard.components import carga_archivos
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("carga")
    carga_archivos.render()
