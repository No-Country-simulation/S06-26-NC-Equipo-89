"""Componente — Temas Recurrentes.

Muestra el análisis cross-tick de categorías que reaparecen con frecuencia,
combinando estadísticas históricas (Parte A) con resumen semántico LLM (Parte B).
"""
from __future__ import annotations

import streamlit as st

from dashboard import theme
from dashboard.theme import CATEGORIA_HINTS


_TENDENCIA_LABEL: dict[str, str] = {
    "subiendo": "en alza",
    "bajando": "en baja",
    "estable": "estable",
    "nuevo": "nuevo en el período",
}

_TENDENCIA_ICON: dict[str, str] = {
    "subiendo": "↑",
    "bajando": "↓",
    "estable": "→",
    "nuevo": "★",
}

_TENDENCIA_COLOR: dict[str, str] = {
    "subiendo": theme.DANGER,
    "bajando": theme.SUCCESS,
    "estable": theme.TEXT_MUTED,
    "nuevo": theme.PRIMARY,
}




def _badge(text: str, bg: str, fg: str) -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:999px;font-size:0.75rem;font-weight:600">{text}</span>'
    )


def _truncate(text: str, max_len: int = 90) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _render_ejemplos_fila(
    *,
    variantes: list[str],
    ejemplos_mensajes: list[str],
) -> None:
    if variantes:
        linea = " · ".join(f"«{_truncate(v)}»" for v in variantes[:5])
        st.markdown(
            f"<small style='color:{theme.TEXT_MUTED}'>"
            f"En patrones del agente: {linea}</small>",
            unsafe_allow_html=True,
        )
        return

    if ejemplos_mensajes:
        linea = " · ".join(f"«{_truncate(m)}»" for m in ejemplos_mensajes[:3])
        st.markdown(
            f"<small style='color:{theme.TEXT_MUTED}'>"
            f"En mensajes clasificados: {linea}</small>",
            unsafe_allow_html=True,
        )


def _temas_ordenados_por_menciones(temas: list[dict]) -> list[dict]:
    """Completa las 10 categorías de la taxonomía y ordena de más a menos menciones."""
    por_nombre = {t.get("categoria"): t for t in temas if t.get("categoria")}
    completos: list[dict] = []

    for categoria in CATEGORIA_HINTS:
        if categoria in por_nombre:
            completos.append(por_nombre[categoria])
        else:
            completos.append({
                "categoria": categoria,
                "menciones": 0,
                "dias_activos": 0,
                "pct_urgencia_alta": 0.0,
                "tendencia": "estable",
                "variantes_semanticas": [],
            })

    completos.sort(
        key=lambda t: (-int(t.get("menciones") or 0), t.get("categoria", "")),
    )
    return completos


def render(data: dict | None) -> None:
    """Renderiza el panel de temas recurrentes.

    Args:
        data: Resultado de ``get_temas_recurrentes()`` o None si no hay datos.
    """
    if data is None:
        st.info(
            "📭 Aún no hay análisis de temas recurrentes guardado. "
            "Ejecutá el job manualmente:\n\n"
            "```bash\n"
            "cd backend && ../.venv/bin/python scripts/recurring_topics_job.py "
            "--days 7 --save --verbose\n"
            "```",
        )
        return

    temas: list[dict] = data.get("temas") or []
    resumen_llm: str | None = data.get("resumen_llm")
    periodo_dias: int = data.get("periodo_dias", 7)
    created_at: str | None = data.get("created_at")

    from dashboard.supabase_queries import format_relative_iso, get_ejemplos_resumen_por_categorias

    ts_label = format_relative_iso(created_at) if created_at else "—"

    st.caption(
        f"Ventana de análisis: últimos **{periodo_dias} días** · "
        f"Actualizado {ts_label}"
    )

    if not temas:
        st.caption("Sin datos del job en este período — se muestran las 10 categorías con 0 menciones.")

    # ── Resumen semántico LLM ────────────────────────────────────────────────
    if resumen_llm:
        st.markdown(
            f'<div style="background:{theme.PRIMARY_SOFT};border-left:4px solid {theme.PRIMARY};'
            f'padding:12px 16px;border-radius:6px;margin-bottom:16px;color:{theme.TEXT}">'
            f"🤖 <strong>Resumen del período:</strong> {resumen_llm}</div>",
            unsafe_allow_html=True,
        )

    with st.expander("¿Qué categorías usa el clasificador?", expanded=False):
        for nombre, hint in CATEGORIA_HINTS.items():
            st.markdown(f"**{nombre}** — {hint}")

    temas_ordenados = _temas_ordenados_por_menciones(temas)
    con_actividad = sum(1 for t in temas_ordenados if int(t.get("menciones") or 0) > 0)

    st.markdown("#### Las 10 categorías del clasificador")
    st.caption(
        f"Ordenadas de más a menos menciones en el período "
        f"({con_actividad} con actividad)."
    )

    todas_cats = tuple(CATEGORIA_HINTS.keys())
    ejemplos_por_cat = get_ejemplos_resumen_por_categorias(todas_cats)

    for tema in temas_ordenados:
        cat = tema.get("categoria", "—")
        menciones = int(tema.get("menciones") or 0)
        dias = int(tema.get("dias_activos") or 0)
        pct_urg = tema.get("pct_urgencia_alta", 0.0)
        tendencia = tema.get("tendencia", "estable")
        variantes = tema.get("variantes_semanticas") or []
        sin_actividad = menciones == 0

        hint = CATEGORIA_HINTS.get(cat)

        with st.container():
            col_cat, col_stats, col_tend = st.columns([3, 3, 2])
            with col_cat:
                st.markdown(f"**{cat}**")
                if hint:
                    st.caption(hint)
            with col_stats:
                st.markdown(
                    f"**{menciones}** menciones · **{dias}** días con actividad",
                    unsafe_allow_html=True,
                )
                if not sin_actividad:
                    urg_bg = theme.DANGER if pct_urg >= 50 else (
                        theme.WARNING if pct_urg >= 25 else "#f1f5f9"
                    )
                    urg_fg = "#fff" if pct_urg >= 50 else (
                        theme.TEXT if pct_urg < 25 else "#7c3516"
                    )
                    urg_badge = _badge(f"{pct_urg:.0f}% urg. Alta", bg=urg_bg, fg=urg_fg)
                    st.markdown(urg_badge, unsafe_allow_html=True)
            with col_tend:
                if sin_actividad:
                    st.caption("Sin actividad")
                else:
                    icon = _TENDENCIA_ICON.get(tendencia, "→")
                    color = _TENDENCIA_COLOR.get(tendencia, theme.TEXT_MUTED)
                    tend_label = _TENDENCIA_LABEL.get(tendencia, tendencia)
                    tend_badge = _badge(f"{icon} {tend_label}", bg="#f1f5f9", fg=color)
                    st.markdown(tend_badge, unsafe_allow_html=True)

            if not sin_actividad:
                _render_ejemplos_fila(
                    variantes=variantes,
                    ejemplos_mensajes=ejemplos_por_cat.get(cat, []),
                )

            st.divider()
