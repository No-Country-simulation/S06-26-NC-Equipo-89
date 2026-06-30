"""Vista — Revisión humana."""

from dashboard.components import revision
from dashboard.layout import render_page_header


def render() -> None:
    render_page_header("revision")
    revision.render()
