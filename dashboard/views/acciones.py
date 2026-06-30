"""Vista — Acciones sugeridas."""

from dashboard.components import acciones
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("acciones")
    acciones.render()
