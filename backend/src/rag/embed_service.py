"""Servicio de indexación incremental de embeddings para RAG."""

import asyncio
import structlog
from src.core.config import settings
from src.core.pgvector import vector_to_pg
from src.tools.cohere_client import cohere_client
from src.tools.supabase_client import get_db

logger = structlog.get_logger()

FETCH_QUERY = """
    SELECT fc.external_id, fr.texto
    FROM feedback_clasificado fc
    JOIN feedback_raw fr ON fr.external_id = fc.external_id
    WHERE fc.embedding IS NULL
    ORDER BY fc.created_at ASC
    LIMIT $1
"""

COUNT_REMAINING_QUERY = """
    SELECT COUNT(*)::int
    FROM feedback_clasificado
    WHERE embedding IS NULL
"""


async def run_embed_indexing() -> int:
    """
    Indexa feedback sin embedding en sub-lotes.
    Retorna la cantidad de registros indexados en esta corrida.
    """
    pool = await get_db()
    total_indexed = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch(FETCH_QUERY, settings.embed_max_per_run)

    if not rows:
        logger.info("embed_job_no_pending")
        return 0

    for i in range(0, len(rows), settings.embed_batch_size):
        batch = rows[i : i + settings.embed_batch_size]
        external_ids = [r["external_id"] for r in batch]
        textos = [r["texto"] for r in batch]

        vectors = await cohere_client.embed_batch(textos)

        async with pool.acquire() as conn:
            async with conn.transaction():
                for external_id, vector in zip(external_ids, vectors):
                    await conn.execute(
                        """
                        UPDATE feedback_clasificado
                        SET embedding = $1::vector
                        WHERE external_id = $2 AND embedding IS NULL
                        """,
                        vector_to_pg(vector),
                        external_id,
                    )

        total_indexed += len(batch)
        logger.info("embed_batch_done", batch_size=len(batch), total_indexed=total_indexed)

        if i + settings.embed_batch_size < len(rows):
            await asyncio.sleep(settings.embed_job_sleep_seconds)

    async with pool.acquire() as conn:
        remaining = await conn.fetchval(COUNT_REMAINING_QUERY)

    logger.info("embed_job_done", indexed_count=total_indexed, remaining=remaining)
    return total_indexed
