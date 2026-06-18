"""Página — Patrones Detectados."""

from dashboard.components import patrones
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("patrones")
    patrones.render()
