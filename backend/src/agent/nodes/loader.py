import structlog
from src.agent.state import FeedbackState
from src.tools.supabase_client import get_db
from src.core.config import settings

logger = structlog.get_logger()

async def loader_node(state: FeedbackState) -> dict:
    pool = await get_db()
    # Micro-batching usando SELECT FOR UPDATE SKIP LOCKED
    query = """
        WITH batch AS (
            SELECT id, external_id, fuente, texto, timestamp, metadata
            FROM feedback_raw
            WHERE estado = 'pendiente'
            ORDER BY timestamp ASC
            LIMIT $1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE feedback_raw
        SET estado = 'procesando'
        FROM batch
        WHERE feedback_raw.id = batch.id
        RETURNING batch.id, batch.external_id, batch.fuente, batch.texto, batch.timestamp, batch.metadata;
    """
    
    async with pool.acquire() as conn:
        records = await conn.fetch(query, settings.batch_size)
        
    current_batch = [dict(r) for r in records]
    
    if not current_batch:
        logger.info("loader_empty_batch")
        return {"current_batch": []}
        
    logger.info("loader_batch_loaded", size=len(current_batch))
    # Inicializamos el resto de llaves para la nueva corrida
    return {
        "current_batch": current_batch,
        "processed_items": [],
        "patterns": [],
        "metrics": {},
        "errors": []
    }
