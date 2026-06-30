"""Componente — Temas Recurrentes.

Muestra el análisis cross-tick de categorías que reaparecen con frecuencia,
combinando estadísticas históricas (Parte A) con resumen semántico LLM (Parte B).
"""
from __future__ import annotations

import streamlit as st

from dashboard import theme


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

    from dashboard.supabase_queries import format_relative_iso

    ts_label = format_relative_iso(created_at) if created_at else "—"

    st.caption(
        f"Ventana de análisis: últimos **{periodo_dias} días** · "
        f"Actualizado {ts_label}"
    )

    if not temas:
        st.warning("No se encontraron categorías con menciones en el período seleccionado.")
        return

    # ── Resumen semántico LLM ────────────────────────────────────────────────
    if resumen_llm:
        st.markdown(
            f'<div style="background:{theme.PRIMARY_SOFT};border-left:4px solid {theme.PRIMARY};'
            f'padding:12px 16px;border-radius:6px;margin-bottom:16px;color:{theme.TEXT}">'
            f"🤖 <strong>Resumen del período:</strong> {resumen_llm}</div>",
            unsafe_allow_html=True,
        )

    # ── Tabla de temas ───────────────────────────────────────────────────────
    st.markdown(f"#### Top {min(len(temas), 10)} temas del período")

    for tema in temas[:10]:
        cat = tema.get("categoria", "—")
        menciones = tema.get("menciones", 0)
        dias = tema.get("dias_activos", 0)
        pct_urg = tema.get("pct_urgencia_alta", 0.0)
        tendencia = tema.get("tendencia", "estable")
        variantes = tema.get("variantes_semanticas") or []
        resumen_tema = tema.get("resumen_tema", "")

        icon = _TENDENCIA_ICON.get(tendencia, "→")
        color = _TENDENCIA_COLOR.get(tendencia, theme.TEXT_MUTED)
        tend_badge = _badge(f"{icon} {tendencia}", bg="#f1f5f9", fg=color)

        urg_bg = theme.DANGER if pct_urg >= 50 else (theme.WARNING if pct_urg >= 25 else "#f1f5f9")
        urg_fg = "#fff" if pct_urg >= 50 else (theme.TEXT if pct_urg < 25 else "#7c3516")
        urg_badge = _badge(f"🚨 {pct_urg:.0f}% urgente", bg=urg_bg, fg=urg_fg)

        with st.container():
            col_cat, col_stats, col_tend = st.columns([3, 3, 2])
            with col_cat:
                st.markdown(f"**{cat}**")
                if resumen_tema:
                    st.caption(resumen_tema)
            with col_stats:
                st.markdown(
                    f"📊 **{menciones}** menciones en **{dias}** días activos",
                    unsafe_allow_html=True,
                )
                st.markdown(urg_badge, unsafe_allow_html=True)
            with col_tend:
                st.markdown(tend_badge, unsafe_allow_html=True)

            if variantes:
                st.markdown(
                    "<small style='color:" + theme.TEXT_MUTED + "'>Variantes: "
                    + " · ".join(f"<em>{v}</em>" for v in variantes)
                    + "</small>",
                    unsafe_allow_html=True,
                )

            st.divider()
