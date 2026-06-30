import asyncio
import json
from datetime import datetime, timezone

import structlog

from src.agent.graph import app
from src.core.config import settings
from src.core.queue_maintenance import recover_stuck_processing
from src.tools.supabase_client import db_client

logger = structlog.get_logger()


async def _last_consistency_run_days() -> float | None:
    """Devuelve días desde la última consistency_run, o None si nunca corrió."""
    try:
        async with db_client.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT created_at FROM feedback_metricas
                WHERE datos_metricas->>'tipo' = 'consistency_run'
                ORDER BY created_at DESC LIMIT 1
                """
            )
        if not row:
            return None
        delta = datetime.now(timezone.utc) - row["created_at"].replace(tzinfo=timezone.utc)
        return delta.total_seconds() / 86400
    except Exception as e:
        logger.warning("consistency_check_last_run_error", error=str(e))
        return None


async def consistency_job() -> None:
    """
    Job paralelo: corre consistency_check cada CONSISTENCY_CHECK_INTERVAL_DAYS días.
    Desactivar con CONSISTENCY_CHECK_INTERVAL_DAYS=0.
    """
    interval_days = settings.consistency_check_interval_days
    if interval_days <= 0:
        logger.info("consistency_job_disabled")
        return

    # Espera inicial para que el worker principal arranque primero
    await asyncio.sleep(60)

    while True:
        try:
            days_since = await _last_consistency_run_days()
            should_run = days_since is None or days_since >= interval_days

            if should_run:
                logger.info(
                    "consistency_check_auto_start",
                    days_since=days_since,
                    interval_days=interval_days,
                )
                from scripts.consistency_check import run_consistency_check

                summary = await run_consistency_check(
                    runs=settings.consistency_check_runs,
                    save_metrics=True,
                    mark_unstable=False,
                    stability_threshold=settings.consistency_check_stability_threshold,
                )
                logger.info(
                    "consistency_check_auto_done",
                    estabilidad=summary.get("estabilidad_promedio"),
                    inestables=len(summary.get("inestables", [])),
                )
            else:
                logger.info(
                    "consistency_check_auto_skip",
                    days_since=round(days_since, 1),
                    next_in_days=round(interval_days - days_since, 1),
                )
        except Exception as e:
            logger.error("consistency_job_error", error=str(e))

        # Revisar una vez al día si toca correr
        await asyncio.sleep(60 * 60 * 24)


async def run_worker_loop():
    """
    Bucle principal del Agente. Corre en segundo plano independientemente
    de FastAPI, consumiendo lotes de Supabase según el intervalo configurado.
    """
    logger.info("worker_starting")
    await db_client.connect()

    from src.tools.gemini_client import gemini_client

    await gemini_client.warm_classification_cache()

    # Job de consistency check en paralelo (no bloquea clasificación)
    asyncio.create_task(consistency_job())

    try:
        while True:
            logger.info("worker_tick_start")

            await recover_stuck_processing()

            initial_state = {"current_batch": []}
            await app.ainvoke(initial_state)

            from src.rag.embed_service import run_embed_indexing

            indexed = await run_embed_indexing()
            if indexed:
                logger.info("worker_embed_indexed", count=indexed)

            logger.info("worker_tick_end")

            intervalo_segundos = settings.batch_interval_minutes * 60
            logger.info("worker_sleeping", seconds=intervalo_segundos)
            await asyncio.sleep(intervalo_segundos)

    except asyncio.CancelledError:
        logger.info("worker_cancelled")
    except Exception as e:
        logger.error("worker_fatal_error", error=str(e))
    finally:
        await db_client.close()
        logger.info("worker_shutdown")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker_loop())
    except KeyboardInterrupt:
        print("\nWorker detenido manualmente.")
