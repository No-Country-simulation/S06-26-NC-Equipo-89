"""
Analiza temas recurrentes cruzando datos históricos de clasificaciones (Parte A — estadística)
con patrones semánticos de ticks anteriores (Parte B — LLM).

Uso manual:
  cd backend && ../.venv/bin/python scripts/recurring_topics_job.py --days 7 --verbose
  cd backend && ../.venv/bin/python scripts/recurring_topics_job.py --days 7 --save

El worker también lo ejecuta automáticamente según RECURRING_TOPICS_INTERVAL_DAYS.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from pydantic import BaseModel
from src.core.config import settings
from src.core.prompt_loader import load_prompt
from src.tools.llm_client import generate_json
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

RECURRING_PROMPT = load_prompt(
    "recurring_topics_v1.md",
    fallback="Analiza categorías recurrentes:\n{stats_tsv}\nPatrones:\n{patrones_txt}",
)


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class TemaLLM(BaseModel):
    categoria: str
    variantes_semanticas: list[str]
    resumen_tema: str


class TemasResult(BaseModel):
    temas: list[TemaLLM]


# ── Parte A — estadística (sin LLM) ──────────────────────────────────────────

async def _fetch_stats(conn, periodo_dias: int) -> list[dict]:
    """Agrega menciones, días activos y % urgencia alta por categoría en el período."""
    rows = await conn.fetch(
        """
        SELECT
            cat_value,
            COUNT(*)                                                          AS menciones,
            COUNT(DISTINCT DATE(fr.timestamp))                                AS dias_activos,
            ROUND(
                AVG(CASE WHEN fc.urgencia = 'Alta' THEN 1.0 ELSE 0.0 END) * 100
            , 1)                                                               AS pct_urgencia_alta
        FROM feedback_clasificado fc
        JOIN feedback_raw fr ON fr.external_id = fc.external_id
        JOIN LATERAL jsonb_array_elements_text(
            CASE
                WHEN jsonb_typeof(fc.categorias) = 'array' THEN fc.categorias
                ELSE '[]'::jsonb
            END
        ) AS cat_value ON TRUE
        WHERE fr.timestamp > NOW() - INTERVAL '1 day' * $1
          AND cat_value IS NOT NULL
          AND cat_value <> ''
        GROUP BY cat_value
        ORDER BY menciones DESC
        LIMIT 15
        """,
        periodo_dias,
    )
    return [dict(r) for r in rows]


async def _fetch_prev_stats(conn, periodo_dias: int) -> dict[str, int]:
    """Menciones por categoría en el período anterior (para calcular tendencia)."""
    rows = await conn.fetch(
        """
        SELECT cat_value, COUNT(*) AS menciones
        FROM feedback_clasificado fc
        JOIN feedback_raw fr ON fr.external_id = fc.external_id
        JOIN LATERAL jsonb_array_elements_text(
            CASE
                WHEN jsonb_typeof(fc.categorias) = 'array' THEN fc.categorias
                ELSE '[]'::jsonb
            END
        ) AS cat_value ON TRUE
        WHERE fr.timestamp BETWEEN NOW() - INTERVAL '1 day' * $1 * 2
                               AND NOW() - INTERVAL '1 day' * $1
          AND cat_value IS NOT NULL
        GROUP BY cat_value
        """,
        periodo_dias,
    )
    return {r["cat_value"]: r["menciones"] for r in rows}


def _tendencia(actual: int, anterior: int | None) -> str:
    if anterior is None or anterior == 0:
        return "nuevo"
    ratio = actual / anterior
    if ratio > 1.15:
        return "subiendo"
    if ratio < 0.85:
        return "bajando"
    return "estable"


async def _fetch_patrones_recientes(conn, n_ticks: int = 5) -> list[str]:
    """Descripciones de patrones de los últimos N ticks."""
    rows = await conn.fetch(
        """
        SELECT descripcion FROM feedback_patrones
        ORDER BY created_at DESC
        LIMIT $1
        """,
        n_ticks * 5,  # hasta 5 patrones por tick
    )
    return [r["descripcion"] for r in rows]


# ── Parte B — semántica (LLM) ────────────────────────────────────────────────

async def _enrich_with_llm(
    stats: list[dict],
    patrones: list[str],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Devuelve (variantes por categoría, resumen por categoría) via LLM."""
    if not stats or not patrones:
        return {}, {}

    stats_tsv = "categoria\tmenciones\tdias_activos\tpct_urgencia_alta\n" + "\n".join(
        f"{s['cat_value']}\t{s['menciones']}\t{s['dias_activos']}\t{s['pct_urgencia_alta']}"
        for s in stats
    )
    patrones_txt = "\n".join(f"- {p}" for p in patrones[:20])

    prompt = RECURRING_PROMPT.format(stats_tsv=stats_tsv, patrones_txt=patrones_txt)

    try:
        result_json = await generate_json(
            prompt=prompt,
            schema=TemasResult,
            cache_profile=None,
        )
        result = json.loads(result_json)
        temas_llm = result.get("temas", [])
        variantes = {t["categoria"]: t.get("variantes_semanticas", []) for t in temas_llm}
        resumenes = {t["categoria"]: t.get("resumen_tema", "") for t in temas_llm}
        return variantes, resumenes
    except Exception as e:
        logger.warning("recurring_topics_llm_failed", error=str(e))
        return {}, {}


# ── Función principal reutilizable ────────────────────────────────────────────

async def run_recurring_topics(
    periodo_dias: int,
    save: bool,
    stability_threshold: float = 0.70,
) -> dict:
    """Núcleo reutilizable por el script manual y el job del worker.

    Conecta una sola vez: fetch → LLM (sin DB) → save → close.
    """
    await db_client.connect()
    try:
        async with db_client.pool.acquire() as conn:
            stats = await _fetch_stats(conn, periodo_dias)
            prev = await _fetch_prev_stats(conn, periodo_dias)
            patrones = await _fetch_patrones_recientes(conn)

        if not stats:
            logger.info("recurring_topics_no_data")
            return {"temas": [], "resumen_llm": None}

        # LLM call — no necesita conexión a DB
        variantes, resumenes = await _enrich_with_llm(stats, patrones)

        temas = []
        for s in stats:
            cat = s["cat_value"]
            temas.append({
                "categoria": cat,
                "menciones": int(s["menciones"]),
                "dias_activos": int(s["dias_activos"]),
                "pct_urgencia_alta": float(s["pct_urgencia_alta"] or 0),
                "tendencia": _tendencia(int(s["menciones"]), prev.get(cat)),
                "variantes_semanticas": variantes.get(cat, []),
                "resumen_tema": resumenes.get(cat, ""),
            })

        resumen_llm = (
            f"Top temas en {periodo_dias} días: "
            + ", ".join(t["categoria"] for t in temas[:5])
            + "."
        ) if temas else None

        if save:
            async with db_client.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO feedback_temas_recurrentes (periodo_dias, temas, resumen_llm)
                    VALUES ($1, $2, $3)
                    """,
                    periodo_dias,
                    json.dumps(temas),
                    resumen_llm,
                )
            logger.info("recurring_topics_saved", total=len(temas))

    finally:
        await db_client.close()

    payload = {
        "tipo": "recurring_topics",
        "periodo_dias": periodo_dias,
        "temas": temas,
        "resumen_llm": resumen_llm,
    }
    return payload


# ── CLI ───────────────────────────────────────────────────────────────────────

async def main(periodo_dias: int, save: bool, verbose: bool) -> None:
    result = await run_recurring_topics(periodo_dias=periodo_dias, save=save)

    if verbose and result["temas"]:
        sep = "-" * 80
        print(sep)
        print(f"{'CATEGORÍA':<25} {'MENCIONES':>10} {'DÍAS':>5} {'URG%':>6} {'TENDENCIA':<12}")
        print(sep)
        for t in result["temas"]:
            tend_icon = {"subiendo": "↑", "bajando": "↓", "estable": "→", "nuevo": "★"}.get(
                t["tendencia"], ""
            )
            print(
                f"{t['categoria']:<25} {t['menciones']:>10} {t['dias_activos']:>5} "
                f"{t['pct_urgencia_alta']:>5.0f}% {tend_icon} {t['tendencia']:<10}"
            )
            if t.get("variantes_semanticas"):
                print(f"  Variantes: {', '.join(t['variantes_semanticas'])}")
            if t.get("resumen_tema"):
                print(f"  Resumen: {t['resumen_tema']}")
        print(sep)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if save:
        print(f"Guardado en feedback_temas_recurrentes. ({len(result['temas'])} temas)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analiza temas recurrentes de feedback.")
    parser.add_argument("--days", type=int, default=settings.recurring_topics_period_days)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.days, args.save, args.verbose))
