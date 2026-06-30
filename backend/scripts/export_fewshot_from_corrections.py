"""
Exporta correcciones humanas a few-shot dinámico para el clasificador.

  cd backend && python scripts/export_fewshot_from_corrections.py
  cd backend && python scripts/export_fewshot_from_corrections.py --limit 10
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
OUTPUT_FILE = PROMPTS_DIR / "classification_fewshot_dynamic.md"

QUERY = """
    SELECT c.texto_original, c.clasificacion_corregida, c.created_at
    FROM feedback_correcciones c
    WHERE c.motivo IN ('correccion_humana', 'confirmacion_humana')
    ORDER BY c.created_at DESC
    LIMIT $1
"""


def _format_example(texto: str, clasificacion: dict, idx: int) -> str:
    salida = json.dumps(clasificacion, ensure_ascii=False)
    return (
        f"## Corrección humana {idx}\n"
        f"Entrada: {texto.strip()}\n"
        f"Salida: {salida}\n"
    )


async def main(limit: int) -> None:
    await db_client.connect()
    try:
        async with db_client.pool.acquire() as conn:
            rows = await conn.fetch(QUERY, limit)
    finally:
        await db_client.close()

    if not rows:
        logger.info("export_fewshot_empty")
        print("No hay correcciones para exportar.")
        return

    blocks = [
        "# Ejemplos aprendidos de correcciones humanas (generado automáticamente)\n",
        "Usa estos pares como referencia adicional de criterio validado por humanos.\n",
    ]
    for i, row in enumerate(rows, start=1):
        corr = row["clasificacion_corregida"]
        if isinstance(corr, str):
            corr = json.loads(corr)
        blocks.append(_format_example(row["texto_original"] or "", corr, i))

    OUTPUT_FILE.write_text("\n".join(blocks), encoding="utf-8")
    logger.info("export_fewshot_done", path=str(OUTPUT_FILE), count=len(rows))
    print(f"Exportados {len(rows)} ejemplos → {OUTPUT_FILE}")
    print("Sugerencia: incrementá GEMINI_CACHE_VERSION en .env y reiniciá el worker.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exportar correcciones a few-shot dinámico")
    parser.add_argument("--limit", type=int, default=10, help="Máximo de correcciones recientes")
    args = parser.parse_args()
    asyncio.run(main(args.limit))
