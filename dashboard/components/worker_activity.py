"""Indicadores visibles de ciclos y reintentos del worker."""

from __future__ import annotations

import streamlit as st

from dashboard.supabase_queries import format_relative_iso, get_worker_activity


def _queue_delta_label(prev: dict[str, int], current: dict[str, int]) -> str | None:
    parts: list[str] = []
    for key, label in (
        ("errores", "errores"),
        ("pendientes", "pendientes"),
        ("procesando", "procesando"),
    ):
        before = prev.get(key, 0)
        after = current.get(key, 0)
        if before != after:
            parts.append(f"{label} {before}→{after}")
    if not parts:
        return None
    return "Δ cola: " + " · ".join(parts)


def render(*, show_delta: bool = True) -> None:
    """Muestra si el agente corrió, está procesando o espera el próximo ciclo."""
    try:
        activity = get_worker_activity()
    except Exception:
        return

    estado = activity.get("estado_agente", "en_espera")
    processing = activity.get("procesando", 0)
    interval = activity.get("intervalo_minutos", 5)
    ultimo_at = activity.get("ultimo_ciclo_at")
    exitos = activity.get("exitos_ultimo_ciclo", 0)
    errores_lote = activity.get("errores_ultimo_ciclo", 0)
    tamano = activity.get("tamano_ultimo_ciclo", 0)
    clas_5m = activity.get("clasificados_ultimos_5m", 0)

    if estado == "procesando":
        label = "mensaje" if processing == 1 else "mensajes"
        st.caption(f"🔄 **Agente activo ahora** — clasificando {processing} {label}.")
    elif estado == "ciclo_reciente" and ultimo_at:
        if tamano > 0:
            resumen = (
                f"último ciclo {format_relative_iso(ultimo_at)}: "
                f"{exitos} OK · {errores_lote} fallidos de {tamano}"
            )
        else:
            resumen = f"último ciclo {format_relative_iso(ultimo_at)}"
        st.caption(f"✅ **Agente corrió** — {resumen}.")
    elif ultimo_at:
        st.caption(
            f"⏳ **Próximo ciclo ~{interval} min** — último intento "
            f"{format_relative_iso(ultimo_at)} "
            f"({exitos} OK, {errores_lote} fallidos)."
        )
    else:
        st.caption(
            f"⏳ **Agente en espera** — ciclos cada ~{interval} min "
            "(aún sin registros de procesamiento)."
        )

    if clas_5m > 0:
        label = "mensaje" if clas_5m == 1 else "mensajes"
        st.caption(f"📥 {clas_5m} {label} clasificados en los últimos 5 min.")

    if show_delta:
        current = {
            "errores": activity.get("errores", 0),
            "pendientes": activity.get("pendientes", 0),
            "procesando": activity.get("procesando", 0),
        }
        prev = st.session_state.get("fc_queue_prev")
        if prev:
            delta = _queue_delta_label(prev, current)
            if delta:
                st.caption(delta)
        st.session_state["fc_queue_prev"] = current
