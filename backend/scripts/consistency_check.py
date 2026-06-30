"""
Mide estabilidad y exactitud del clasificador enviando cada mensaje del golden set N veces.

Uso manual:
  cd backend && python scripts/consistency_check.py
  cd backend && python scripts/consistency_check.py --runs 5 --save-metrics
  cd backend && python scripts/consistency_check.py --runs 3 --save-metrics --mark-unstable

El worker también lo ejecuta automáticamente según CONSISTENCY_CHECK_INTERVAL_DAYS.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.agent.nodes.classifier import CLASSIFICATION_SYSTEM, classify_single
from src.core.config import settings
from src.core.llm_usage import UsageStats
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_classifications.json"


def _load_golden() -> list[dict]:
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return data["examples"]


def _field_stability(values: list[str]) -> float:
    """Fracción de runs que coinciden con el valor más frecuente."""
    if not values:
        return 0.0
    most_common_count = Counter(values).most_common(1)[0][1]
    return round(most_common_count / len(values) * 100, 1)


def _majority(values: list[str]) -> str:
    if not values:
        return ""
    return Counter(values).most_common(1)[0][0]


async def run_consistency_check(
    runs: int,
    save_metrics: bool,
    mark_unstable: bool,
    stability_threshold: float,
) -> dict:
    """
    Núcleo reutilizable por el script manual y el job automático del worker.
    Devuelve el dict de resultados (mismo formato que --save-metrics).
    """
    examples = _load_golden()
    usage = UsageStats()
    per_example: list[dict] = []

    for ex in examples:
        item = {"external_id": ex["id"], "texto": ex["texto"]}
        sentimientos: list[str] = []
        urgencias: list[str] = []
        categorias_runs: list[frozenset] = []
        confianzas: list[float] = []
        errores = 0

        for _ in range(runs):
            outcome = await classify_single(item, CLASSIFICATION_SYSTEM, usage_stats=usage)
            if outcome.get("status") != "success":
                errores += 1
                continue
            c = outcome.get("classification") or {}
            sentimientos.append(c.get("sentimiento", ""))
            urgencias.append(c.get("urgencia", ""))
            categorias_runs.append(frozenset(c.get("categorias") or []))
            if c.get("confianza") is not None:
                confianzas.append(float(c["confianza"]))

        cats_str = [",".join(sorted(s)) for s in categorias_runs]
        stab_sent = _field_stability(sentimientos)
        stab_urg = _field_stability(urgencias)
        stab_cats = _field_stability(cats_str)
        stab_overall = round((stab_sent + stab_urg + stab_cats) / 3, 1)

        maj_sent = _majority(sentimientos)
        maj_urg = _majority(urgencias)
        exact_sent = maj_sent.strip().lower() == ex["sentimiento"].strip().lower()
        exact_urg = maj_urg.strip().lower() == ex["urgencia"].strip().lower()
        exp_cats = set(c.strip() for c in (ex.get("categorias") or []))
        maj_cats = set(_majority(cats_str).split(",")) if cats_str else set()
        exact_cats = exp_cats == maj_cats

        per_example.append({
            "id": ex["id"],
            "runs_ok": runs - errores,
            "estabilidad_overall": stab_overall,
            "estabilidad_sentimiento": stab_sent,
            "estabilidad_urgencia": stab_urg,
            "estabilidad_categorias": stab_cats,
            "exactitud_sentimiento": exact_sent,
            "exactitud_urgencia": exact_urg,
            "exactitud_categorias": exact_cats,
            "confianza_promedio": round(sum(confianzas) / len(confianzas), 3) if confianzas else None,
            "confianza_min": round(min(confianzas), 3) if confianzas else None,
            "confianza_max": round(max(confianzas), 3) if confianzas else None,
            "inestable": stab_overall < (stability_threshold * 100),
        })

    total = len(per_example)
    inestables = [e["id"] for e in per_example if e["inestable"]]

    def _avg_pct(key: str) -> float:
        vals = [e[key] for e in per_example]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    def _exact_pct(key: str) -> float:
        vals = [e[key] for e in per_example]
        return round(sum(1 for v in vals if v) / len(vals) * 100, 1) if vals else 0.0

    summary = {
        "tipo": "consistency_run",
        "runs": runs,
        "total": total,
        "estabilidad_promedio": _avg_pct("estabilidad_overall"),
        "exact_match_pct": round(
            sum(1 for e in per_example if e["exactitud_sentimiento"] and e["exactitud_urgencia"] and e["exactitud_categorias"])
            / total * 100, 1
        ) if total else 0.0,
        "por_campo": {
            "sentimiento": {
                "estabilidad": _avg_pct("estabilidad_sentimiento"),
                "exactitud": _exact_pct("exactitud_sentimiento"),
            },
            "urgencia": {
                "estabilidad": _avg_pct("estabilidad_urgencia"),
                "exactitud": _exact_pct("exactitud_urgencia"),
            },
            "categorias": {
                "estabilidad": _avg_pct("estabilidad_categorias"),
                "exactitud": _exact_pct("exactitud_categorias"),
            },
        },
        "inestables": inestables,
    }

    if save_metrics or mark_unstable:
        await db_client.connect()
        try:
            async with db_client.pool.acquire() as conn:
                if save_metrics:
                    await conn.execute(
                        "INSERT INTO feedback_metricas (datos_metricas) VALUES ($1)",
                        json.dumps(summary),
                    )
                    logger.info("consistency_check_saved", total=total, inestables=len(inestables))

                if mark_unstable and inestables:
                    await conn.executemany(
                        """
                        UPDATE feedback_clasificado
                        SET requiere_revision = true,
                            motivo_revision = 'inestabilidad'
                        WHERE external_id = $1
                        """,
                        [(eid,) for eid in inestables],
                    )
                    logger.info("consistency_check_marked_unstable", count=len(inestables))
        finally:
            await db_client.close()

    return summary


async def main(runs: int, save_metrics: bool, mark_unstable: bool, verbose: bool) -> None:
    examples = _load_golden()
    golden_by_id = {ex["id"]: ex for ex in examples}
    usage = UsageStats()
    per_example: list[dict] = []

    for ex in examples:
        item = {"external_id": ex["id"], "texto": ex["texto"]}
        sentimientos: list[str] = []
        urgencias: list[str] = []
        categorias_runs: list[frozenset] = []
        confianzas: list[float] = []
        errores = 0

        for _ in range(runs):
            outcome = await classify_single(item, CLASSIFICATION_SYSTEM, usage_stats=usage)
            if outcome.get("status") != "success":
                errores += 1
                continue
            c = outcome.get("classification") or {}
            sentimientos.append(c.get("sentimiento", ""))
            urgencias.append(c.get("urgencia", ""))
            categorias_runs.append(frozenset(c.get("categorias") or []))
            if c.get("confianza") is not None:
                confianzas.append(float(c["confianza"]))

        cats_str = [",".join(sorted(s)) for s in categorias_runs]
        stab_sent = _field_stability(sentimientos)
        stab_urg = _field_stability(urgencias)
        stab_cats = _field_stability(cats_str)
        stab_overall = round((stab_sent + stab_urg + stab_cats) / 3, 1)

        maj_sent = _majority(sentimientos)
        maj_urg = _majority(urgencias)
        maj_cats_str = _majority(cats_str)
        maj_cats = set(maj_cats_str.split(",")) if maj_cats_str else set()

        exp = golden_by_id[ex["id"]]
        exact_sent = maj_sent.strip().lower() == exp["sentimiento"].strip().lower()
        exact_urg = maj_urg.strip().lower() == exp["urgencia"].strip().lower()
        exp_cats = set(c.strip() for c in (exp.get("categorias") or []))
        exact_cats = exp_cats == maj_cats

        per_example.append({
            "id": ex["id"],
            "texto": ex["texto"][:60],
            "esperado_sent": exp["sentimiento"],
            "modelo_sent": maj_sent,
            "exact_sent": exact_sent,
            "esperado_urg": exp["urgencia"],
            "modelo_urg": maj_urg,
            "exact_urg": exact_urg,
            "esperado_cats": sorted(exp_cats),
            "modelo_cats": sorted(maj_cats),
            "exact_cats": exact_cats,
            "estabilidad": stab_overall,
            "confianza_promedio": round(sum(confianzas) / len(confianzas), 2) if confianzas else None,
            "inestable": stab_overall < (settings.consistency_check_stability_threshold * 100),
        })

    if verbose:
        sep = "-" * 90
        print(sep)
        print(f"{'ID':<14} {'TEXTO':<42} {'SENT':^5} {'URG':^5} {'CATS':^5}  CONF")
        print(sep)
        for e in per_example:
            sent_ok = "✓" if e["exact_sent"] else "✗"
            urg_ok  = "✓" if e["exact_urg"]  else "✗"
            cats_ok = "✓" if e["exact_cats"] else "✗"
            conf    = f"{e['confianza_promedio']:.2f}" if e["confianza_promedio"] else "  — "
            flag    = " ⚠ INEST." if e["inestable"] else ""
            print(f"{e['id']:<14} {e['texto']:<42} {sent_ok:^5} {urg_ok:^5} {cats_ok:^5}  {conf}{flag}")
            if not e["exact_cats"]:
                print(f"  {'':14} esperado cats: {e['esperado_cats']}")
                print(f"  {'':14} modelo   cats: {e['modelo_cats']}")
        print(sep)

    # Calcular summary igual que run_consistency_check
    total = len(per_example)
    inestables = [e["id"] for e in per_example if e["inestable"]]

    def _avg(key: str) -> float:
        vals = [e[key] for e in per_example]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    def _exact_pct(key: str) -> float:
        vals = [e[key] for e in per_example]
        return round(sum(1 for v in vals if v) / len(vals) * 100, 1) if vals else 0.0

    summary = {
        "tipo": "consistency_run",
        "runs": runs,
        "total": total,
        "estabilidad_promedio": _avg("estabilidad"),
        "exact_match_pct": round(
            sum(1 for e in per_example if e["exact_sent"] and e["exact_urg"] and e["exact_cats"])
            / total * 100, 1
        ) if total else 0.0,
        "por_campo": {
            "sentimiento": {"estabilidad": 0.0, "exactitud": _exact_pct("exact_sent")},
            "urgencia":    {"estabilidad": 0.0, "exactitud": _exact_pct("exact_urg")},
            "categorias":  {"estabilidad": 0.0, "exactitud": _exact_pct("exact_cats")},
        },
        "inestables": inestables,
    }

    if not verbose:
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

    if mark_unstable and inestables:
        print(f"Marcados para revisión: {', '.join(inestables)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mide estabilidad del clasificador con el golden set.")
    parser.add_argument("--runs", type=int, default=settings.consistency_check_runs)
    parser.add_argument("--save-metrics", action="store_true")
    parser.add_argument("--mark-unstable", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Tabla detallada por mensaje")
    args = parser.parse_args()
    asyncio.run(main(args.runs, args.save_metrics, args.mark_unstable, args.verbose))
