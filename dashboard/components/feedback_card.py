"""Cards HTML para mensajes clasificados — módulo independiente de ui.py."""

from __future__ import annotations

from dashboard.theme import IMPACT_BADGES, SENTIMENT_COLORS, SOURCE_BADGES


def _badge(label: str, bg: str, color: str) -> str:
    return (
        f'<span class="fc-badge" style="background:{bg}; color:{color};">'
        f"{label}</span>"
    )


def _source_badge(fuente: str) -> str:
    key = (fuente or "csv").lower().strip()
    label, bg, color = SOURCE_BADGES.get(key, (fuente or "Otro", "#f1f5f9", "#475569"))
    return _badge(label, bg, color)


def _sentiment_badge(sentimiento: str) -> str:
    color = SENTIMENT_COLORS.get(sentimiento, "#94a3b8")
    return _badge(sentimiento or "—", f"{color}22", color)


def _urgency_badge(urgencia: str) -> str:
    _label, bg, color = IMPACT_BADGES.get(urgencia, ("—", "#f1f5f9", "#475569"))
    return _badge(urgencia or "—", bg, color)


from shared.confidence import get_confidence_review_threshold, is_high_confidence


def _confidence_badge(confianza: float | None) -> str:
    threshold = get_confidence_review_threshold()
    if confianza is None:
        return _badge("Conf. —", "#f1f5f9", "#475569")
    pct = confianza * 100 if confianza <= 1 else confianza
    if not is_high_confidence(confianza, threshold):
        return _badge(f"Conf. {pct:.0f}% · revisar", "#fee2e2", "#991b1b")
    return _badge(f"Conf. {pct:.0f}%", "#dcfce7", "#166534")


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
            _badge(c, "#eff6ff", "#1e40af") for c in categorias if c
        ) or _badge("Sin categoría", "#f1f5f9", "#64748b")
    else:
        cat_html = _badge(str(categorias or "Sin categoría"), "#f1f5f9", "#64748b")

    texto_safe = (texto or "").replace("<", "&lt;").replace(">", "&gt;")
    resumen_safe = (resumen or "—").replace("<", "&lt;").replace(">", "&gt;")

    return f"""
    <div class="fc-feedback-card">
        <div class="fc-feedback-header">
            <span class="fc-feedback-id">{external_id}</span>
            <span class="fc-feedback-date">{fecha}</span>
        </div>
        <div class="fc-feedback-badges">
            {_source_badge(fuente)}
            {_sentiment_badge(sentimiento)}
            {_urgency_badge(urgencia)}
            {_confidence_badge(confianza)}
            {_badge(idioma or "—", "#f1f5f9", "#475569")}
        </div>
        <p class="fc-feedback-resumen"><strong>Resumen:</strong> {resumen_safe}</p>
        <p class="fc-feedback-texto">{texto_safe}</p>
        <div class="fc-feedback-cats">{cat_html}</div>
    </div>
    """
