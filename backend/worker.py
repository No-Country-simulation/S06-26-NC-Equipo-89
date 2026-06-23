import asyncio
import structlog
from src.agent.graph import app
from src.tools.supabase_client import db_client
from src.core.config import settings

logger = structlog.get_logger()

async def run_worker_loop():
    """
    Bucle principal del Agente. Corre en segundo plano independientemente
    de FastAPI, consumiendo lotes de Supabase según el intervalo configurado.
    """
    logger.info("worker_starting")
    await db_client.connect()

    from src.tools.gemini_client import gemini_client

    await gemini_client.warm_classification_cache()
    
    try:
        while True:
            logger.info("worker_tick_start")
            
            # Estado inicial vacío. El loader_node se encargará de ir a Supabase.
            initial_state = {"current_batch": []}
            
            # Ejecutamos la máquina de estados de LangGraph de forma asíncrona
            final_state = await app.ainvoke(initial_state)

            # Indexar embeddings de items recién clasificados (RAG Copilot)
            from src.rag.embed_service import run_embed_indexing

            indexed = await run_embed_indexing()
            if indexed:
                logger.info("worker_embed_indexed", count=indexed)
            
            logger.info("worker_tick_end")
            
            # Pausa (ej. 5 minutos) antes de buscar el siguiente lote (ADR-006)
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
