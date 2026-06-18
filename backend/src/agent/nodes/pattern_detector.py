import structlog
import json
from pathlib import Path
from pydantic import BaseModel
from typing import List
from src.agent.state import FeedbackState
from src.tools.llm_client import generate_json

logger = structlog.get_logger()

PROMPT_PATH = Path("prompts/pattern_summary_v1.md")

class Pattern(BaseModel):
    descripcion: str
    frecuencia_estimada: str
    nivel_impacto: str

class PatternResult(BaseModel):
    patrones: List[Pattern]

def load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Detecta patrones en estos datos: {datos}"

async def pattern_detector_node(state: FeedbackState) -> dict:
    processed = state.get("processed_items", [])
    if not processed:
        return {"patterns": []}
        
    logger.info("pattern_detector_start")
    
    template = load_prompt_template()
    textos = [item["classification"] for item in processed]
    
    prompt = template.format(datos=json.dumps(textos))
    
    try:
        result_json = await generate_json(prompt=prompt, schema=PatternResult)
        result = json.loads(result_json)
        patterns = result.get("patrones", [])
        logger.info("pattern_detector_done", count=len(patterns))
        return {"patterns": patterns}
    except Exception as e:
        logger.error("pattern_detector_failed", error=str(e))
        return {"patterns": []}
