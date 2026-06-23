import csv
import io
import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from shared.ingest_fields import SOURCE_FIELD_ALIASES, TEXT_FIELD_ALIASES, pick_field
from src.api.deps import rate_limit_ingest, verify_api_key
from src.schemas.feedback import FeedbackPayload
from src.tools.supabase_client import get_db

logger = structlog.get_logger()
router = APIRouter()

INSERT_QUERY = """
    INSERT INTO feedback_raw (external_id, fuente, texto, timestamp, metadata, estado)
    VALUES ($1, $2, $3, $4, $5, 'pendiente')
    ON CONFLICT (external_id) DO NOTHING
"""


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_feedback(
    payload: FeedbackPayload,
    request: Request,
    db=Depends(get_db),
    _=Depends(verify_api_key),
    __=Depends(rate_limit_ingest),
):
    """
    Recibe payload de n8n, lo valida y lo inserta en feedback_raw (ADR-006).
    """
    try:
        result = await db.execute(
            INSERT_QUERY,
            payload.external_id,
            payload.fuente,
            payload.texto,
            payload.timestamp,
            json.dumps(payload.metadata),
        )
        if result == "INSERT 0":
            logger.info("ingest_duplicate", external_id=payload.external_id)
            return {"status": "duplicate", "id": payload.external_id}
        logger.info("ingest_success", external_id=payload.external_id)
        return {"status": "success", "id": payload.external_id}
    except Exception as e:
        logger.error("ingest_failed", error=str(e), external_id=payload.external_id)
        raise HTTPException(status_code=500, detail="Database insertion failed")


@router.post("/ingest/csv", status_code=status.HTTP_202_ACCEPTED)
async def ingest_csv(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
    _=Depends(verify_api_key),
    __=Depends(rate_limit_ingest),
):
    """
    Recibe CSV desde Streamlit, parsea filas y las encola en feedback_raw.
    Columnas: texto (obligatorio), fuente (opcional), external_id (opcional).
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo .csv")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="El CSV debe estar en UTF-8")

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
    has_text = any(alias in fieldnames for alias in TEXT_FIELD_ALIASES)
    if not reader.fieldnames or not has_text:
        raise HTTPException(
            status_code=400,
            detail="El CSV debe incluir columna 'texto' (o alias: content, message, comentario)",
        )

    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    async with db.acquire() as conn:
        async with conn.transaction():
            for row in reader:
                texto = pick_field(row, TEXT_FIELD_ALIASES)
                if not texto:
                    skipped += 1
                    continue

                external_id = pick_field(row, ("external_id",)) or f"csv-{uuid.uuid4()}"
                fuente = pick_field(row, SOURCE_FIELD_ALIASES) or "csv"

                result = await conn.execute(
                    INSERT_QUERY,
                    external_id,
                    fuente,
                    texto,
                    now,
                    json.dumps({"source": "csv_upload", "filename": file.filename}),
                )
                if result == "INSERT 0":
                    skipped += 1
                else:
                    inserted += 1

    logger.info("ingest_csv_done", inserted=inserted, skipped=skipped)
    return {"status": "success", "inserted": inserted, "skipped": skipped}
