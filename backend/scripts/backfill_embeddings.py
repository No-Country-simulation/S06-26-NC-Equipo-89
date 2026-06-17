"""
Backfill one-shot de embeddings para datos históricos.
Ejecutar una vez tras aplicar la migración 005_rag_copilot.sql.

  cd backend && python scripts/backfill_embeddings.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.rag.embed_service import run_embed_indexing
from src.tools.supabase_client import db_client

logger = structlog.get_logger()


async def main() -> None:
    logger.info("backfill_starting")
    await db_client.connect()
    total = 0
    try:
        while True:
            indexed = await run_embed_indexing()
            if indexed == 0:
                break
            total += indexed
            logger.info("backfill_progress", total_indexed=total)
    finally:
        await db_client.close()
    logger.info("backfill_finished", total_indexed=total)


if __name__ == "__main__":
    asyncio.run(main())
