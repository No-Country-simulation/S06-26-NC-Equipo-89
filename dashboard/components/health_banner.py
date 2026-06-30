"""Banner global de salud del pipeline y servicios."""

from __future__ import annotations

import streamlit as st

from dashboard.health import check_fastapi_health
from dashboard.supabase_queries import get_kpis, get_queue_health


def render(*, show_fastapi: bool = True) -> None:
    """
    Muestra banners según estado de cola, FastAPI y Supabase.

    Args:
        show_fastapi: Si False, omite aviso FastAPI (p.ej. páginas sin API).
    """
    pending = 0
    processing = 0
    errors = 0
    acciones = 0
    revision = 0
    supabase_ok = True

    try:
        health = get_queue_health()
        kpis = get_kpis()
        pending = health["pendientes"]
        processing = health.get("procesando", 0)
        errors = health["errores"]
        acciones = kpis.get("acciones_abiertas", 0)
        revision = kpis.get("pendientes_revision", 0)
    except EnvironmentError as e:
        supabase_ok = False
        st.error(f"{e} — Revisá SUPABASE_URL y SUPABASE_KEY en .env")
        return
    except Exception as e:
        supabase_ok = False
        st.error(f"No se pudo conectar con Supabase: {e}")
        return

    if acciones > 0:
        label = "acción" if acciones == 1 else "acciones"
        st.warning(
            f"**{acciones} {label} sugerida(s) pendiente(s)** — "
            "revisá la página **Acciones sugeridas** en el menú."
        )

    if revision > 0:
        label = "mensaje" if revision == 1 else "mensajes"
        st.info(
            f"**{revision} {label} requieren revisión humana** — "
            "andá a **Revisar clasificaciones** para confirmar o corregir."
        )

    if errors > 0:
        label = "mensaje" if errors == 1 else "mensajes"
        st.error(
            f"**{errors} {label} con error de clasificación** — "
            "el agente los reintenta automáticamente cada ~5 min "
            "(prioridad sobre pendientes). Si persisten, revisá cuota Gemini/Groq "
            "en los logs del worker."
        )

    if processing > 0:
        label = "mensaje" if processing == 1 else "mensajes"
        st.info(
            f"**{processing} {label} en procesamiento** — el worker los está clasificando ahora."
        )

    if pending > 0:
        label = "mensaje" if pending == 1 else "mensajes"
        st.info(
            f"**{pending} {label} en cola** — el agente los procesará en el próximo ciclo (~5 min)."
        )

    if show_fastapi and supabase_ok:
        ok, msg = check_fastapi_health()
        if not ok:
            st.warning(msg)
