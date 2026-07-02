"""Ejecutar evaluación y consistency check desde el dashboard."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends

from src.api.deps import verify_api_key
from src.core.config import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/eval")
async def run_eval(_: str = Depends(verify_api_key)) -> dict:
    """Clasifica el golden set una vez y guarda métricas de exactitud."""
    from scripts.eval_classification import run_eval_classification

    logger.info("quality_eval_manual_start")
    summary = await run_eval_classification(save_metrics=True)
    logger.info("quality_eval_manual_done", exact_match_pct=summary.get("exact_match_pct"))
    return summary


@router.post("/consistency")
async def run_consistency(_: str = Depends(verify_api_key)) -> dict:
    """Clasifica el golden set N veces y guarda métricas de estabilidad."""
    from scripts.consistency_check import run_consistency_check

    logger.info(
        "quality_consistency_manual_start",
        runs=settings.consistency_check_runs,
    )
    summary = await run_consistency_check(
        runs=settings.consistency_check_runs,
        save_metrics=True,
        mark_unstable=False,
        stability_threshold=settings.consistency_check_stability_threshold,
    )
    logger.info(
        "quality_consistency_manual_done",
        estabilidad=summary.get("estabilidad_promedio"),
    )
    return summary
