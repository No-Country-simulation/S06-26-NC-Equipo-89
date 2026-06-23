import json
import structlog
from pydantic import BaseModel
from typing import List

from src.agent.state import FeedbackState
from src.core.llm_compact import classifications_to_tsv
from src.core.prompt_loader import load_prompt
from src.tools.llm_client import generate_json

logger = structlog.get_logger()

PATTERN_SYSTEM = load_prompt(
    "pattern_summary_v2.md",
    fallback="Identifica patrones en el TSV:\n{datos}",
)


class Pattern(BaseModel):
    descripcion: str
    frecuencia_estimada: str
    nivel_impacto: str


class PatternResult(BaseModel):
    patrones: List[Pattern]


async def pattern_detector_node(state: FeedbackState) -> dict:
    processed = state.get("processed_items", [])
    if not processed:
        return {"patterns": []}

    logger.info("pattern_detector_start", prompt_mode="tsv_v2")

    tsv_data = classifications_to_tsv(processed)
    user_prompt = PATTERN_SYSTEM.format(datos=tsv_data)

    try:
        result_json = await generate_json(
            prompt=user_prompt,
            schema=PatternResult,
            cache_profile=None,
        )
        result = json.loads(result_json)
        patterns = result.get("patrones", [])
        logger.info("pattern_detector_done", count=len(patterns))
        return {"patterns": patterns}
    except Exception as e:
        logger.error("pattern_detector_failed", error=str(e))
        return {"patterns": []}
