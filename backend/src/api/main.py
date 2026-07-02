import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import classifications, copilot, ingest, quality
from src.core.config import settings
from src.tools.supabase_client import db_client, get_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_startup", env=settings.env)
    if settings.is_production:
        logger.info("api_production_mode", log_pii=settings.log_pii)
    await db_client.connect()
    yield
    logger.info("api_shutdown")
    await db_client.close()


app = FastAPI(
    title="Feedback Classifier API",
    description="Gateway de ingesta para feedback procesado por LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["X-API-Key", "Content-Type"],
    )

app.include_router(ingest.router, tags=["ingest"])
app.include_router(classifications.router)
app.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
app.include_router(quality.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/deep")
async def health_check_deep():
    """Ping a PostgreSQL — útil para healthchecks de despliegue."""
    try:
        pool = await get_db()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("health_deep_failed", error=str(exc))
        return {"status": "degraded", "database": "unavailable"}
