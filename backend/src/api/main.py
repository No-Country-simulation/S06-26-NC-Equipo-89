import structlog
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import ingest, copilot
from src.tools.supabase_client import db_client

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("api_startup")
    await db_client.connect()
    yield
    # Shutdown
    logger.info("api_shutdown")
    await db_client.close()

app = FastAPI(
    title="Feedback Classifier API",
    description="Gateway de ingesta para feedback procesado por LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingest.router, tags=["ingest"])
app.include_router(copilot.router, prefix="/copilot", tags=["copilot"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
