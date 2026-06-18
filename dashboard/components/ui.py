"""Componentes UI reutilizables — Dashboard v3."""

from pathlib import Path

import streamlit as st

from dashboard.theme import SOURCE_BADGES, STYLES_DIR


def inject_styles() -> None:
    """Inyecta CSS global del design system y tema activo."""
    css_path = STYLES_DIR / "custom.css"
    theme = st.session_state.get("theme", "light")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.markdown(
        f'<script>document.documentElement.setAttribute("data-theme","{theme}");</script>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None) -> None:
    """Encabezado principal de la página activa."""
    st.markdown(f'<p class="fc-page-title">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="fc-page-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str | None = None) -> None:
    """Encabezado de sección dentro de un componente."""
    st.markdown(f'<p class="fc-section-title">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def empty_state(message: str, *, cta_label: str | None = None, cta_key: str | None = None) -> None:
    """Estado vacío estilizado con CTA opcional."""
    st.markdown(f'<div class="fc-empty">{message}</div>', unsafe_allow_html=True)
    if cta_label and cta_key:
        if st.button(cta_label, key=cta_key, type="primary"):
            st.session_state["_nav_target"] = "carga"
            st.rerun()


def badge(label: str, bg: str, color: str) -> str:
    """HTML de badge para cards."""
    return (
        f'<span class="fc-badge" style="background:{bg}; color:{color};">'
        f"{label}</span>"
    )


def source_badge(fuente: str) -> str:
    """Badge HTML según fuente del feedback."""
    key = (fuente or "csv").lower().strip()
    label, bg, color = SOURCE_BADGES.get(key, (fuente or "Otro", "#f1f5f9", "#475569"))
    return badge(label, bg, color)


def source_card(external_id: str, sentimiento: str, similarity: float, texto: str) -> str:
    """Card HTML compacta para fuente citada del Copilot."""
    preview = texto[:180] + ("..." if len(texto) > 180 else "")
    return f"""
    <div class="fc-source-card">
        <div class="fc-source-card-header">
            <span class="fc-source-card-id">{external_id}</span>
            <span class="fc-source-card-meta">{sentimiento} · sim {similarity:.0%}</span>
        </div>
        <p class="fc-source-card-text">{preview}</p>
    </div>
    """


def metric_card(
    label: str,
    value: str,
    *,
    delta: str | None = None,
    delta_color: str = "normal",
    help_text: str | None = None,
) -> None:
    """Wrapper semántico sobre st.metric."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)


def skeleton_metrics(n: int = 4) -> None:
    """Placeholders mientras cargan KPIs."""
    cols = st.columns(n)
    for col in cols:
        with col:
            st.markdown(
                """
                <div class="fc-skeleton-metric">
                    <div class="fc-skeleton-line fc-skeleton-label"></div>
                    <div class="fc-skeleton-line fc-skeleton-value"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def pattern_card(description: str, badges_html: str) -> None:
    """Card de patrón detectado."""
    st.markdown(
        f"""
        <div class="fc-card">
            <p class="fc-card-text">{description}</p>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">{badges_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def brand_sidebar(logo_path: Path, title: str, subtitle: str) -> None:
    """Logo y marca en sidebar."""
    if logo_path.exists():
        st.image(str(logo_path), width=56)
    st.markdown(f'<p class="fc-brand-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="fc-brand-sub">{subtitle}</p>', unsafe_allow_html=True)


def scope_badge(label: str) -> None:
    """Badge de alcance temporal del Copilot."""
    st.markdown(
        f'<span class="fc-scope-badge">{label}</span>',
        unsafe_allow_html=True,
    )


def sentiment_badge(sentimiento: str) -> str:
    """Badge de sentimiento."""
    from dashboard.theme import SENTIMENT_COLORS

    color = SENTIMENT_COLORS.get(sentimiento, "#94a3b8")
    bg = f"{color}22"
    return badge(sentimiento or "—", bg, color)


def urgency_badge(urgencia: str) -> str:
    """Badge de urgencia."""
    from dashboard.theme import IMPACT_BADGES

    _label, bg, color = IMPACT_BADGES.get(urgencia, ("—", "#f1f5f9", "#475569"))
    return badge(urgencia or "—", bg, color)


def confidence_badge(confianza: float | None) -> str:
    """Badge de confianza; resalta valores bajos (< 0.7)."""
    if confianza is None:
        return badge("Conf. —", "#f1f5f9", "#475569")
    pct = confianza * 100 if confianza <= 1 else confianza
    if confianza < 0.7:
        return badge(f"Conf. {pct:.0f}% · revisar", "#fee2e2", "#991b1b")
    return badge(f"Conf. {pct:.0f}%", "#dcfce7", "#166534")


def feedback_card_html(
    *,
    external_id: str,
    fuente: str,
    sentimiento: str,
    urgencia: str,
    confianza: float | None,
    idioma: str,
    resumen: str,
    texto: str,
    categorias: list[str] | str,
    fecha: str,
) -> str:
    """Card HTML para un mensaje clasificado."""
    if isinstance(categorias, list):
        cat_html = " ".join(
            badge(c, "#eff6ff", "#1e40af") for c in categorias if c
        ) or badge("Sin categoría", "#f1f5f9", "#64748b")
    else:
        cat_html = badge(str(categorias or "Sin categoría"), "#f1f5f9", "#64748b")

    texto_safe = (texto or "").replace("<", "&lt;").replace(">", "&gt;")
    resumen_safe = (resumen or "—").replace("<", "&lt;").replace(">", "&gt;")

    return f"""
    <div class="fc-feedback-card">
        <div class="fc-feedback-header">
            <span class="fc-feedback-id">{external_id}</span>
            <span class="fc-feedback-date">{fecha}</span>
        </div>
        <div class="fc-feedback-badges">
            {source_badge(fuente)}
            {sentiment_badge(sentimiento)}
            {urgency_badge(urgencia)}
            {confidence_badge(confianza)}
            {badge(idioma or "—", "#f1f5f9", "#475569")}
        </div>
        <p class="fc-feedback-resumen"><strong>Resumen:</strong> {resumen_safe}</p>
        <p class="fc-feedback-texto">{texto_safe}</p>
        <div class="fc-feedback-cats">{cat_html}</div>
    </div>
    """
