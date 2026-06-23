"""Formateo de fechas y valores para la UI."""

from __future__ import annotations

import pandas as pd


def format_fecha(value: str) -> str:
    """Timestamp ISO o texto → dd/mm/YYYY HH:MM."""
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return str(value or "—")
    return ts.strftime("%d/%m/%Y %H:%M")
