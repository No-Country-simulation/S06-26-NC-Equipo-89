import structlog
from src.agent.state import FeedbackState
from src.tools.supabase_client import get_db
from src.core.config import settings

logger = structlog.get_logger()


async def loader_node(state: FeedbackState) -> dict:
    pool = await get_db()
    # Micro-batching: errores primero (reintento automático), luego pendientes.
    query = """
        WITH batch AS (
            SELECT id, external_id, fuente, texto, timestamp, metadata, estado
            FROM feedback_raw
            WHERE estado IN ('error', 'pendiente')
            ORDER BY
                CASE WHEN estado = 'error' THEN 0 ELSE 1 END,
                timestamp ASC
            LIMIT $1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE feedback_raw
        SET estado = 'procesando',
            retry_count = CASE
                WHEN batch.estado = 'error' THEN 0
                ELSE feedback_raw.retry_count
            END,
            error_mensaje = CASE
                WHEN batch.estado = 'error' THEN NULL
                ELSE feedback_raw.error_mensaje
            END
        FROM batch
        WHERE feedback_raw.id = batch.id
        RETURNING batch.id, batch.external_id, batch.fuente, batch.texto,
                  batch.timestamp, batch.metadata, batch.estado AS previous_estado;
    """

    async with pool.acquire() as conn:
        records = await conn.fetch(query, settings.batch_size)

    current_batch = [
        {k: v for k, v in dict(r).items() if k != "previous_estado"}
        for r in records
    ]
    requeued_from_error = sum(
        1 for r in records if dict(r).get("previous_estado") == "error"
    )

    if not current_batch:
        logger.info("loader_empty_batch")
        return {"current_batch": []}

    logger.info(
        "loader_batch_loaded",
        size=len(current_batch),
        requeued_from_error=requeued_from_error,
    )
    # Inicializamos el resto de llaves para la nueva corrida
    return {
        "current_batch": current_batch,
        "processed_items": [],
        "patterns": [],
        "metrics": {},
        "errors": [],
        "actions": [],
    }
