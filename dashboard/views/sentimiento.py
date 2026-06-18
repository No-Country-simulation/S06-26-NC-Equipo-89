"""Página — Sentimiento y Categorías."""

from dashboard.components import sentimiento
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("sentimiento")
    sentimiento.render()
