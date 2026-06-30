"""Umbral de confianza compartido backend / dashboard."""

from __future__ import annotations

import os


def get_confidence_review_threshold() -> float:
    """Umbral por debajo del cual un mensaje requiere revisión humana."""
    raw = os.getenv("CONFIDENCE_REVIEW_THRESHOLD", "0.7")
    try:
        value = float(raw)
        return min(1.0, max(0.0, value))
    except ValueError:
        return 0.7


def is_high_confidence(confianza: float | None, threshold: float | None = None) -> bool:
    """True si la confianza es >= umbral."""
    if confianza is None:
        return False
    t = threshold if threshold is not None else get_confidence_review_threshold()
    score = confianza if confianza <= 1 else confianza / 100
    return score >= t
