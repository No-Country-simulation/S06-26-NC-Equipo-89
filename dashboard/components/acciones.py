"""Bandeja de acciones sugeridas por el agente."""

from __future__ import annotations

import streamlit as st

from dashboard.components.ui import section_header
from dashboard.supabase_queries import get_acciones_pendientes, get_acciones_resumen, schema_migration_hint

_TIPO_LABELS = {
    "urgente": "Urgente",
    "revision": "Revisión",
    "patron": "Patrón",
    "oportunidad": "Oportunidad",
}

_TIPO_ICONS = {
    "urgente": "🔴",
    "revision": "🟡",
    "patron": "🔍",
    "oportunidad": "🟢",
}


def render() -> None:
    section_header(
        "Acciones sugeridas",
        "Tareas concretas generadas por el agente — no solo métricas.",
    )

    hint = schema_migration_hint()
    if hint and "008" in hint:
        st.warning(hint)
        return

    try:
        acciones = get_acciones_pendientes()
        resumen = get_acciones_resumen()
    except Exception as e:
        st.error(f"No se pudieron cargar las acciones: {e}")
        return

    if not acciones:
        st.success("No hay acciones pendientes — cola de trabajo al día.")
        return

    if resumen:
        chips = " · ".join(
            f"{_TIPO_ICONS.get(k, '•')} {_TIPO_LABELS.get(k, k)}: {v}"
            for k, v in sorted(resumen.items())
        )
        st.caption(chips)

    for acc in acciones:
        tipo = acc.get("tipo", "")
        icon = _TIPO_ICONS.get(tipo, "•")
        label = _TIPO_LABELS.get(tipo, tipo)
        with st.expander(f"{icon} [{label}] {acc.get('titulo', 'Sin título')}", expanded=False):
            if acc.get("descripcion"):
                st.write(acc["descripcion"])
            if acc.get("external_id"):
                st.caption(f"Mensaje: `{acc['external_id']}`")
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Prioridad: {acc.get('prioridad', 50)}")
            with col2:
                st.caption(f"Creada: {acc.get('created_at', '')[:19]}")
