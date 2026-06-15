import asyncio
import structlog
import json
from pathlib import Path
from src.agent.state import FeedbackState
from src.tools.gemini_client import gemini_client
from src.schemas.results import FeedbackClassification
from src.core.config import settings

logger = structlog.get_logger()

# Ruta estática al archivo de prompt
PROMPT_PATH = Path("prompts/classification_v1.md")

def load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    # Fallback de seguridad
    return "Clasifica el siguiente texto: {texto}"

async def classify_single(item: dict, template: str) -> dict:
    try:
        # Inyectar el texto real en el template
        prompt = template.format(texto=item['texto'])
        
        result_json = await gemini_client.generate_json(
            prompt=prompt, 
            schema=FeedbackClassification
        )
        
        classification = json.loads(result_json)
        
        return {
            "external_id": item["external_id"],
            "classification": classification,
            "status": "success"
        }
    except Exception as e:
        logger.error("classify_item_error", external_id=item.get("external_id"), error=str(e))
        return {
            "external_id": item.get("external_id"),
            "error": str(e),
            "status": "error"
        }

async def classifier_node(state: FeedbackState) -> dict:
    batch = state.get("current_batch", [])
    if not batch:
        return {"processed_items": []}
        
    logger.info("classifier_start", batch_size=len(batch))
    
    # Cargar el template una sola vez para todo el batch
    template = load_prompt_template()
    
    # Semáforo para respetar la concurrencia (ADR-006)
    sem = asyncio.Semaphore(settings.gemini_concurrency)
    
    async def sem_task(item):
        async with sem:
            return await classify_single(item, template)
            
    results = await asyncio.gather(*(sem_task(item) for item in batch))
    
    processed_items = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    
    logger.info("classifier_done", success_count=len(processed_items), error_count=len(errors))
    
    return {"processed_items": processed_items, "errors": errors}
