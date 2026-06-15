import asyncpg
import structlog
import json
from src.core.config import settings

logger = structlog.get_logger()

class DBClient:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=settings.db_dsn)
            logger.info("db_connected")

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("db_closed")

db_client = DBClient()

async def get_db():
    if not db_client.pool:
        await db_client.connect()
    return db_client.pool
