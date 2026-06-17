"""
Job de indexación de embeddings — ejecutar 3 veces al día vía cron.

Cron sugerido:
  0 8,14,20 * * * cd /path/to/project/backend && python embed_job.py
"""
import asyncio
import structlog
from src.rag.embed_service import run_embed_indexing
from src.tools.supabase_client import db_client

logger = structlog.get_logger()


async def main() -> None:
    logger.info("embed_job_starting")
    await db_client.connect()
    try:
        indexed = await run_embed_indexing()
        logger.info("embed_job_finished", indexed_count=indexed)
    finally:
        await db_client.close()


if __name__ == "__main__":
    asyncio.run(main())
