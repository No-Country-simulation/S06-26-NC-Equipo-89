"""Señales del agente — resumen accionable del último procesamiento (no tickets de CS)."""

from __future__ import annotations

import streamlit as st

from dashboard.components.ui import section_header
from dashboard.supabase_queries import (
    get_acciones_pendientes,
    get_acciones_resumen,
    marcar_accion_estado,
    schema_migration_hint,
)

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

_TIPO_GUIA: dict[str, str] = {
    "urgente": "El agente detectó varias quejas negativas con urgencia Alta en un lote. "
    "Revisá la pestaña **Urgentes**.",
    "revision": "Hay clasificaciones con baja confianza. La acción humana del proyecto es "
    "**Clasificaciones → Revisar** (confirmar o corregir).",
    "patron": "Se detectó un patrón de alto impacto. Más detalle en **Tendencias → Patrones**.",
    "oportunidad": "Varios mensajes positivos comparten categoría. Explorá en **Clasificaciones → Mensajes**.",
}


def render() -> None:
    section_header(
        "Señales del agente",
        "Resumen de lo que el worker priorizó al procesar lotes — monitoreo, no asignación a CS.",
    )

    hint = schema_migration_hint()
    if hint and "008" in hint:
        st.warning(hint)
        return

    st.caption(
        "Cada señal se genera automáticamente tras un tick del pipeline. "
        "Marcá **Vista** cuando ya la revisaste; eso limpia el contador del banner."
    )

    try:
        acciones = get_acciones_pendientes()
        resumen = get_acciones_resumen()
    except Exception as e:
        st.error(f"No se pudieron cargar las señales: {e}")
        return

    if not acciones:
        st.success("Sin señales pendientes — el agente no reportó nada nuevo por revisar aquí.")
        return

    if resumen:
        chips = " · ".join(
            f"{_TIPO_ICONS.get(k, '•')} {_TIPO_LABELS.get(k, k)}: {v}"
            for k, v in sorted(resumen.items())
        )
        st.caption(chips)

    tipos = ["Todos"] + sorted({a.get("tipo", "") for a in acciones if a.get("tipo")})
    filtro = st.radio("Filtrar por tipo", tipos, horizontal=True, key="acciones_tipo_filtro")
    visibles = acciones if filtro == "Todos" else [a for a in acciones if a.get("tipo") == filtro]

    for acc in visibles:
        tipo = acc.get("tipo", "")
        icon = _TIPO_ICONS.get(tipo, "•")
        label = _TIPO_LABELS.get(tipo, tipo)
        accion_id = acc.get("id")
        titulo = acc.get("titulo", "Sin título")

        with st.expander(f"{icon} [{label}] {titulo}", expanded=False):
            guia = _TIPO_GUIA.get(tipo)
            if guia:
                st.info(guia)

            if acc.get("descripcion"):
                st.write(acc["descripcion"])
            if acc.get("external_id"):
                st.caption(f"Mensaje relacionado: `{acc['external_id']}`")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"Prioridad: {acc.get('prioridad', 50)}")
            with col2:
                st.caption(f"Generada: {str(acc.get('created_at', ''))[:19]}")

            if accion_id is not None:
                with col3:
                    c_vista, c_desc = st.columns(2)
                    with c_vista:
                        if st.button("Vista", key=f"acc_hecha_{accion_id}", help="Marcar como revisada"):
                            ok, msg = marcar_accion_estado(int(accion_id), "hecha")
                            if ok:
                                st.rerun()
                            else:
                                st.error(msg)
                    with c_desc:
                        if st.button("Descartar", key=f"acc_desc_{accion_id}", help="Ignorar esta señal"):
                            ok, msg = marcar_accion_estado(int(accion_id), "descartada")
                            if ok:
                                st.rerun()
                            else:
                                st.error(msg)
