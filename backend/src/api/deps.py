"""Dependencias compartidas de rutas FastAPI."""

import structlog
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import settings

logger = structlog.get_logger()
api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifica header X-API-Key para clientes autorizados (n8n, dashboard)."""
    if api_key != settings.api_key:
        logger.warning("auth_failed", reason="invalid_api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
