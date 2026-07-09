"""Filtros compartidos para bandejas de mensajes."""

from __future__ import annotations

import pandas as pd
import streamlit as st

PAGE_SIZE_OPTIONS: tuple[int, ...] = (25, 50, 100, 250, 500, 1000)

TRENDS_PERIOD_LABELS: tuple[str, ...] = (
    "Último análisis",
    "Últimos 7 días",
    "Últimos 30 días",
    "Últimos 90 días",
    "Todo el historial",
)

TRENDS_PERIOD_VALUES: dict[str, str | int] = {
    "Último análisis": "latest",
    "Últimos 7 días": 7,
    "Últimos 30 días": 30,
    "Últimos 90 días": 90,
    "Todo el historial": "all",
}


def _default_page_size(filtered_count: int) -> int:
    if filtered_count <= 0:
        return PAGE_SIZE_OPTIONS[0]
    for opt in reversed(PAGE_SIZE_OPTIONS):
        if opt <= filtered_count:
            return opt
    return PAGE_SIZE_OPTIONS[0]


def _resolve_date_series(df: pd.DataFrame) -> pd.Series | None:
    work = df.copy()
    if "clasificado_at" in work.columns:
        work["_fecha"] = pd.to_datetime(work["clasificado_at"], errors="coerce")
    elif "timestamp" in work.columns:
        work["_fecha"] = pd.to_datetime(work["timestamp"], errors="coerce")
    else:
        return None
    return work["_fecha"]


def filter_dataframe_by_date(df: pd.DataFrame, *, key_prefix: str) -> pd.DataFrame:
    """Filtra por rango de fechas (clasificado_at o timestamp del mensaje)."""
    date_col = _resolve_date_series(df)
    if date_col is None:
        return df

    min_d = date_col.min()
    max_d = date_col.max()
    if pd.isna(min_d) or pd.isna(max_d):
        return df

    date_range = st.date_input(
        "Rango de fechas",
        value=(min_d.date(), max_d.date()),
        key=f"{key_prefix}_date_range",
    )
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        return df

    start, end = date_range
    mask = (date_col.dt.date >= start) & (date_col.dt.date <= end)
    return df.loc[mask].copy()


def render_trends_period_filter(*, key_prefix: str) -> tuple[str, int | None]:
    """Selector de período para vistas de tendencias (temas / patrones).

    Returns:
        (mode, days) con mode en ``latest``, ``days`` o ``all``.
    """
    label = st.selectbox(
        "Período",
        options=list(TRENDS_PERIOD_VALUES.keys()),
        key=f"{key_prefix}_period",
    )
    value = TRENDS_PERIOD_VALUES[label]
    if value == "latest":
        return "latest", None
    if value == "all":
        return "all", None
    return "days", int(value)


def resolve_display_limit(filtered_count: int, *, key_prefix: str) -> int:
    """Control de cuántos mensajes renderizar (slider o todos los filtrados)."""
    col_slider, col_all = st.columns([3, 1])
    with col_all:
        show_all = st.checkbox(
            "Mostrar todos",
            key=f"{key_prefix}_show_all",
            help="Muestra todos los mensajes que pasen los filtros actuales.",
        )
    with col_slider:
        if show_all:
            st.caption(f"Se mostrarán los **{filtered_count}** mensajes filtrados.")
            return max(filtered_count, 0)
        return st.select_slider(
            "Mensajes a mostrar",
            options=list(PAGE_SIZE_OPTIONS),
            value=_default_page_size(filtered_count),
            key=f"{key_prefix}_page_size",
        )
