"""Operaciones de mantenimiento de la cola feedback_raw."""

from __future__ import annotations

import structlog

from src.core.config import settings
from src.tools.supabase_client import get_db

logger = structlog.get_logger()

RECOVER_STUCK_SQL = """
    UPDATE feedback_raw
    SET estado = 'pendiente'
    WHERE estado = 'procesando'
      AND created_at < NOW() - ($1::text || ' minutes')::interval
"""


async def recover_stuck_processing(stale_minutes: int | None = None) -> int:
    """Reencola filas en procesando más antiguas que stale_minutes."""
    minutes = stale_minutes if stale_minutes is not None else settings.stuck_processing_minutes
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute(RECOVER_STUCK_SQL, str(minutes))
    count = int(result.split()[-1]) if result and result.split()[-1].isdigit() else 0
    if count:
        logger.warning("recover_stuck_processing", recovered=count, stale_minutes=minutes)
    return count
