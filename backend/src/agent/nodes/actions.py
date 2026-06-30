"""Genera acciones sugeridas a partir de clasificaciones y patrones del lote."""

from __future__ import annotations

from collections import Counter

import structlog

from src.agent.state import FeedbackState
from src.core.config import settings

logger = structlog.get_logger()


def _needs_review(confianza: float | None) -> bool:
    if confianza is None:
        return True
    score = confianza if confianza <= 1 else confianza / 100
    return score < settings.confidence_review_threshold


async def actions_node(state: FeedbackState) -> dict:
    processed = state.get("processed_items", [])
    patterns = state.get("patterns", [])
    if not processed and not patterns:
        return {"actions": []}

    actions: list[dict] = []

    urgent = [
        p
        for p in processed
        if p["classification"].get("urgencia") == "Alta"
        and p["classification"].get("sentimiento") == "Negativo"
    ]
    if urgent:
        cats: Counter[str] = Counter()
        for item in urgent:
            cats.update(item["classification"].get("categorias") or [])
        top_cat = cats.most_common(1)[0][0] if cats else "general"
        sample_ids = ", ".join(i["external_id"] for i in urgent[:5])
        actions.append(
            {
                "external_id": urgent[0]["external_id"],
                "tipo": "urgente",
                "titulo": f"Atención urgente: {len(urgent)} queja(s) negativa(s)",
                "descripcion": (
                    f"Revisar categoría «{top_cat}». "
                    f"Mensajes: {sample_ids}"
                    + ("…" if len(urgent) > 5 else "")
                ),
                "prioridad": 10,
            }
        )

    for item in processed:
        conf = item["classification"].get("confianza")
        if _needs_review(conf):
            pct = (conf or 0) * 100 if (conf or 0) <= 1 else (conf or 0)
            actions.append(
                {
                    "external_id": item["external_id"],
                    "tipo": "revision",
                    "titulo": "Clasificación dudosa — confirmar",
                    "descripcion": (
                        f"Confianza {pct:.0f}%. "
                        f"{item['classification'].get('resumen', '')[:180]}"
                    ),
                    "prioridad": 30,
                }
            )

    for pat in patterns:
        impact = pat.get("nivel_impacto", "")
        if impact in ("Alto", "Alta"):
            desc = pat.get("descripcion", "")[:120]
            actions.append(
                {
                    "external_id": None,
                    "tipo": "patron",
                    "titulo": f"Patrón de alto impacto: {desc}",
                    "descripcion": f"Frecuencia estimada: {pat.get('frecuencia_estimada', 'N/A')}",
                    "prioridad": 20,
                }
            )

    positive = [p for p in processed if p["classification"].get("sentimiento") == "Positivo"]
    if positive:
        cat_counter: Counter[str] = Counter()
        for item in positive:
            cat_counter.update(item["classification"].get("categorias") or [])
        for cat, count in cat_counter.items():
            if count >= 2:
                actions.append(
                    {
                        "external_id": positive[0]["external_id"],
                        "tipo": "oportunidad",
                        "titulo": f"Oportunidad: replicar experiencia en «{cat}»",
                        "descripcion": (
                            f"{count} mensajes positivos mencionan «{cat}» en este lote."
                        ),
                        "prioridad": 40,
                    }
                )

    logger.info("actions_generated", count=len(actions))
    return {"actions": actions}
