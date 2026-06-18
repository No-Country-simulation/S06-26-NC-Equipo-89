"""Banner global de salud del pipeline y servicios."""

from __future__ import annotations

import streamlit as st

from dashboard.health import check_fastapi_health
from dashboard.supabase_queries import get_pending_count


def render(*, show_fastapi: bool = True) -> None:
    """
    Muestra banners según estado de cola, FastAPI y Supabase.

    Args:
        show_fastapi: Si False, omite aviso FastAPI (p.ej. páginas sin API).
    """
    pending = 0
    supabase_ok = True

    try:
        pending = get_pending_count()
    except EnvironmentError as e:
        supabase_ok = False
        st.error(f"{e} — Revisá SUPABASE_URL y SUPABASE_KEY en .env")
        return
    except Exception as e:
        supabase_ok = False
        st.error(f"No se pudo conectar con Supabase: {e}")
        return

    if pending > 0:
        label = "mensaje" if pending == 1 else "mensajes"
        st.info(
            f"**{pending} {label} en cola** — el agente los procesará en el próximo ciclo (~5 min)."
        )

    if show_fastapi and supabase_ok:
        ok, msg = check_fastapi_health()
        if not ok:
            st.warning(msg)
