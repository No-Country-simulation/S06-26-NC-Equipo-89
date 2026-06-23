"""Dependencias compartidas de rutas FastAPI."""

import structlog
from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from src.api.rate_limit import check_rate_limit
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


async def rate_limit_ingest(request: Request) -> None:
    check_rate_limit(request, "ingest", settings.rate_limit_ingest_per_minute)


async def rate_limit_copilot(request: Request) -> None:
    check_rate_limit(request, "copilot", settings.rate_limit_copilot_per_minute)
