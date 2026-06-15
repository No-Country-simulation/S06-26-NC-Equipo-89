import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Security
from fastapi.security import APIKeyHeader
from src.schemas.feedback import FeedbackPayload
from src.tools.supabase_client import get_db
from src.core.config import settings
import json

logger = structlog.get_logger()
router = APIRouter()

# Definición de seguridad: El header esperado
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verifica que el request provenga de n8n o un cliente autorizado."""
    if api_key != settings.api_key:
        logger.warning("auth_failed", reason="invalid_api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_feedback(
    payload: FeedbackPayload, 
    db=Depends(get_db),
    _=Depends(verify_api_key) # <-- Protege el endpoint
):
    """
    Recibe payload de n8n, lo valida estrcitamente y lo inserta
    en feedback_raw en estado 'pendiente' (Micro-batching ADR-006).
    Requiere header X-API-Key.
    """
    query = """
        INSERT INTO feedback_raw (external_id, fuente, texto, timestamp, metadata, estado)
        VALUES ($1, $2, $3, $4, $5, 'pendiente')
        ON CONFLICT (external_id) DO NOTHING
    """
    try:
        await db.execute(
            query,
            payload.external_id,
            payload.fuente,
            payload.texto,
            payload.timestamp,
            json.dumps(payload.metadata)
        )
        logger.info("ingest_success", external_id=payload.external_id)
        return {"status": "success", "id": payload.external_id}
    except Exception as e:
        logger.error("ingest_failed", error=str(e), external_id=payload.external_id)
        raise HTTPException(status_code=500, detail="Database insertion failed")
