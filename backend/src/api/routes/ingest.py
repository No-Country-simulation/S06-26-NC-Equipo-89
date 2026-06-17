import csv
import io
import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Security, UploadFile, status
from fastapi.security import APIKeyHeader

from src.core.config import settings
from src.schemas.feedback import FeedbackPayload
from src.tools.supabase_client import get_db

logger = structlog.get_logger()
router = APIRouter()

api_key_header = APIKeyHeader(name="X-API-Key")

INSERT_QUERY = """
    INSERT INTO feedback_raw (external_id, fuente, texto, timestamp, metadata, estado)
    VALUES ($1, $2, $3, $4, $5, 'pendiente')
    ON CONFLICT (external_id) DO NOTHING
"""


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifica que el request provenga de n8n o un cliente autorizado."""
    if api_key != settings.api_key:
        logger.warning("auth_failed", reason="invalid_api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_feedback(
    payload: FeedbackPayload,
    db=Depends(get_db),
    _=Depends(verify_api_key),
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
    file: UploadFile = File(...),
    db=Depends(get_db),
    _=Depends(verify_api_key),
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
    if not reader.fieldnames or "texto" not in reader.fieldnames:
        raise HTTPException(status_code=400, detail="El CSV debe incluir columna 'texto'")

    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    async with db.acquire() as conn:
        async with conn.transaction():
            for row in reader:
                texto = (row.get("texto") or "").strip()
                if not texto:
                    skipped += 1
                    continue

                external_id = (row.get("external_id") or "").strip() or f"csv-{uuid.uuid4()}"
                fuente = (row.get("fuente") or "").strip() or "csv"

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
