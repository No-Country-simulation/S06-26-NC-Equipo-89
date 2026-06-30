"""
Evalúa precisión del clasificador contra un golden set local.

  cd backend && python scripts/eval_classification.py
  cd backend && python scripts/eval_classification.py --save-metrics
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.agent.nodes.classifier import CLASSIFICATION_SYSTEM, classify_single
from src.core.llm_usage import UsageStats
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_classifications.json"


def _load_golden() -> list[dict]:
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return data["examples"]


def _match_field(expected: str, actual: str) -> bool:
    return expected.strip().lower() == actual.strip().lower()


def _score_example(expected: dict, result: dict) -> dict:
    c = result.get("classification") or {}
    fields = {
        "sentimiento": _match_field(expected["sentimiento"], c.get("sentimiento", "")),
        "urgencia": _match_field(expected["urgencia"], c.get("urgencia", "")),
    }
    exp_cats = set(expected.get("categorias") or [])
    act_cats = set(c.get("categorias") or [])
    fields["categorias"] = exp_cats == act_cats if exp_cats else bool(act_cats) == bool(act_cats)
    conf = c.get("confianza")
    fields["confianza_alta"] = conf is not None and conf >= 0.7
    return fields


async def main(save_metrics: bool) -> None:
    examples = _load_golden()
    usage = UsageStats()
    results: list[dict] = []

    for ex in examples:
        item = {"external_id": ex["id"], "texto": ex["texto"]}
        outcome = await classify_single(item, CLASSIFICATION_SYSTEM, usage_stats=usage)
        if outcome.get("status") != "success":
            results.append({"id": ex["id"], "ok": False, "error": outcome.get("error")})
            continue
        fields = _score_example(ex, outcome)
        results.append({"id": ex["id"], "ok": all(fields.values()), "fields": fields})

    total = len(results)
    ok = sum(1 for r in results if r.get("ok"))
    by_field: dict[str, list[bool]] = {}
    for r in results:
        for k, v in (r.get("fields") or {}).items():
            by_field.setdefault(k, []).append(v)

    summary = {
        "total": total,
        "exact_match": ok,
        "exact_match_pct": round(ok / total * 100, 1) if total else 0,
        "por_campo": {
            k: round(sum(vals) / len(vals) * 100, 1) for k, vals in by_field.items()
        },
        "tipo": "eval_run",
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if save_metrics:
        await db_client.connect()
        try:
            async with db_client.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO feedback_metricas (datos_metricas) VALUES ($1)",
                    json.dumps(summary),
                )
        finally:
            await db_client.close()
        print("Resultado guardado en feedback_metricas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluar clasificador contra golden set")
    parser.add_argument(
        "--save-metrics",
        action="store_true",
        help="Persistir resultado en feedback_metricas",
    )
    args = parser.parse_args()
    asyncio.run(main(args.save_metrics))
