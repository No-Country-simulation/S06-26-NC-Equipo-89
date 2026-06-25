"""
Reencola feedback en estado 'error' para reproceso inmediato (sin esperar al worker).

El worker ya reintenta errores automáticamente en cada tick (loader prioriza estado
'error' antes que 'pendiente'). Usá este script solo para forzar reencolado manual.

  cd backend && python scripts/requeue_errors.py
  cd backend && python scripts/requeue_errors.py --external-id ma_561108ea2711
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

REQUEUE_ALL = """
    UPDATE feedback_raw
    SET estado = 'pendiente', retry_count = 0, error_mensaje = NULL
    WHERE estado = 'error'
"""

REQUEUE_ONE = """
    UPDATE feedback_raw
    SET estado = 'pendiente', retry_count = 0, error_mensaje = NULL
    WHERE external_id = $1 AND estado = 'error'
"""


async def main(external_id: str | None) -> None:
    await db_client.connect()
    try:
        async with db_client.pool.acquire() as conn:
            if external_id:
                result = await conn.execute(REQUEUE_ONE, external_id)
                logger.info("requeue_one", external_id=external_id, result=result)
            else:
                result = await conn.execute(REQUEUE_ALL)
                logger.info("requeue_all", result=result)
            pending = await conn.fetchval(
                "SELECT COUNT(*) FROM feedback_raw WHERE estado = 'pendiente'"
            )
            errors = await conn.fetchval(
                "SELECT COUNT(*) FROM feedback_raw WHERE estado = 'error'"
            )
            logger.info("queue_status", pendientes=pending, errores=errors)
    finally:
        await db_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reencolar feedback_raw en error")
    parser.add_argument(
        "--external-id",
        help="Solo reencolar este external_id (opcional)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.external_id))
