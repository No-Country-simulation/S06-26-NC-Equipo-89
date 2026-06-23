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
