import json
import uuid

import structlog

from src.agent.state import FeedbackState
from src.core.config import settings
from src.tools.supabase_client import get_db

logger = structlog.get_logger()


async def persister_node(state: FeedbackState) -> dict:
    batch = state.get("current_batch", [])
    processed = state.get("processed_items", [])
    errors = state.get("errors", [])
    patterns = state.get("patterns", [])
    metrics = state.get("metrics", {})

    if not batch:
        return {}

    tick_id = uuid.uuid4()
    pool = await get_db()

    async with pool.acquire() as conn:
        async with conn.transaction():
            success_ids = [item["external_id"] for item in processed]

            if success_ids:
                await conn.execute(
                    "UPDATE feedback_raw SET estado = 'procesado', error_mensaje = NULL WHERE external_id = ANY($1)",
                    success_ids,
                )

            for err in errors:
                external_id = err.get("external_id")
                if not external_id:
                    continue
                await conn.execute(
                    """
                    UPDATE feedback_raw
                    SET retry_count = retry_count + 1,
                        error_mensaje = $2,
                        estado = CASE
                            WHEN retry_count + 1 < $3 THEN 'pendiente'
                            ELSE 'error'
                        END
                    WHERE external_id = $1
                    """,
                    external_id,
                    err.get("error", "unknown error"),
                    settings.max_retries,
                )

            if processed:
                records = []
                for p in processed:
                    c = p["classification"]
                    records.append((
                        p["external_id"],
                        c["sentimiento"],
                        c["urgencia"],
                        c["idioma"],
                        json.dumps(c.get("categorias", [])),
                        c.get("confianza"),
                        c.get("resumen"),
                    ))

                await conn.executemany(
                    """
                    INSERT INTO feedback_clasificado
                        (external_id, sentimiento, urgencia, idioma, categorias, confianza, resumen)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (external_id) DO UPDATE SET
                        sentimiento = EXCLUDED.sentimiento,
                        urgencia = EXCLUDED.urgencia,
                        idioma = EXCLUDED.idioma,
                        categorias = EXCLUDED.categorias,
                        confianza = EXCLUDED.confianza,
                        resumen = EXCLUDED.resumen
                    """,
                    records,
                )

            if metrics:
                await conn.execute(
                    "INSERT INTO feedback_metricas (datos_metricas, tick_id) VALUES ($1, $2)",
                    json.dumps(metrics),
                    tick_id,
                )

            if patterns:
                pattern_records = [
                    (p["descripcion"], p["frecuencia_estimada"], p["nivel_impacto"], tick_id)
                    for p in patterns
                ]
                await conn.executemany(
                    """
                    INSERT INTO feedback_patrones (descripcion, frecuencia, impacto, tick_id)
                    VALUES ($1, $2, $3, $4)
                    """,
                    pattern_records,
                )

    logger.info(
        "persister_done",
        saved_count=len(processed),
        error_count=len(errors),
        tick_id=str(tick_id),
    )
    return {"current_batch": []}
