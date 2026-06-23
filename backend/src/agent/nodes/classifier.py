import asyncio
import json
import structlog
from random import uniform

from src.agent.state import FeedbackState
from src.core.config import settings
from src.core.llm_compact import build_batch_classify_prompt, chunk_for_llm_batch
from src.core.llm_usage import UsageStats
from src.core.prompt_loader import load_prompt
from src.schemas.results import BatchClassificationResult, FeedbackClassification
from src.tools.llm_client import generate_json, _is_retryable

logger = structlog.get_logger()

CLASSIFICATION_SYSTEM = load_prompt(
    "classification_system_v2.md",
    fallback=(
        "Clasifica feedback: sentimiento Positivo|Negativo|Neutral, "
        "urgencia Alta|Media|Baja, categorias, idioma, confianza 0-1, resumen."
    ),
)


def _success_item(external_id: str, classification: dict) -> dict:
    return {
        "external_id": external_id,
        "classification": classification,
        "status": "success",
    }


def _error_item(external_id: str, error: str) -> dict:
    return {
        "external_id": external_id,
        "error": error,
        "status": "error",
    }


def _parse_batch_resultados(resultados: list[dict], chunk: list[dict]) -> list[dict]:
    expected_ids = {item["external_id"] for item in chunk}
    by_id = {row["external_id"]: row for row in resultados if row.get("external_id")}
    if set(by_id.keys()) != expected_ids:
        missing = expected_ids - set(by_id.keys())
        extra = set(by_id.keys()) - expected_ids
        raise ValueError(f"batch_id_mismatch missing={missing} extra={extra}")

    processed: list[dict] = []
    for item in chunk:
        ext_id = item["external_id"]
        row = by_id[ext_id]
        classification = {
            "sentimiento": row["sentimiento"],
            "categorias": row.get("categorias", []),
            "urgencia": row["urgencia"],
            "idioma": row["idioma"],
            "confianza": row["confianza"],
            "resumen": row["resumen"],
        }
        processed.append(_success_item(ext_id, classification))
    return processed


async def classify_single(
    item: dict,
    system_instruction: str,
    usage_stats: UsageStats | None = None,
) -> dict:
    external_id = item.get("external_id")
    user_prompt = item["texto"]
    last_error: Exception | None = None

    for attempt in range(settings.classify_retry_attempts):
        try:
            result_json = await generate_json(
                prompt=user_prompt,
                schema=FeedbackClassification,
                system_instruction=system_instruction,
                usage_stats=usage_stats,
            )
            classification = json.loads(result_json)
            return _success_item(external_id, classification)
        except Exception as e:
            last_error = e
            if attempt + 1 >= settings.classify_retry_attempts or not _is_retryable(e):
                break
            delay = settings.classify_retry_base_seconds * (2**attempt) + uniform(0, 1)
            logger.warning(
                "classify_item_retry",
                external_id=external_id,
                attempt=attempt + 1,
                delay_seconds=round(delay, 2),
                error=str(e),
            )
            await asyncio.sleep(delay)

    logger.error("classify_item_error", external_id=external_id, error=str(last_error))
    return _error_item(external_id, str(last_error))


async def classify_batch_chunk(
    chunk: list[dict],
    system_instruction: str,
    usage_stats: UsageStats | None = None,
) -> list[dict]:
    """Clasifica un micro-lote; fallback 1-a-1 si falla validación o LLM."""
    if len(chunk) == 1:
        return [await classify_single(chunk[0], system_instruction, usage_stats)]

    user_prompt = build_batch_classify_prompt(chunk)
    last_error: Exception | None = None

    for attempt in range(settings.classify_retry_attempts):
        try:
            result_json = await generate_json(
                prompt=user_prompt,
                schema=BatchClassificationResult,
                system_instruction=system_instruction,
                usage_stats=usage_stats,
            )
            data = json.loads(result_json)
            resultados = data.get("resultados", [])
            return _parse_batch_resultados(resultados, chunk)
        except Exception as e:
            last_error = e
            if attempt + 1 >= settings.classify_retry_attempts or not _is_retryable(e):
                break
            delay = settings.classify_retry_base_seconds * (2**attempt) + uniform(0, 1)
            logger.warning(
                "classify_batch_retry",
                chunk_size=len(chunk),
                attempt=attempt + 1,
                delay_seconds=round(delay, 2),
                error=str(e),
            )
            await asyncio.sleep(delay)

    logger.warning(
        "classify_batch_fallback_single",
        chunk_size=len(chunk),
        error=str(last_error),
    )
    results: list[dict] = []
    for item in chunk:
        results.append(await classify_single(item, system_instruction, usage_stats))
    return results


async def classifier_node(state: FeedbackState) -> dict:
    batch = state.get("current_batch", [])
    if not batch:
        return {"processed_items": []}

    usage = UsageStats()
    batch_size = settings.classify_llm_batch_size
    mode = "micro_batch" if batch_size > 1 else "single"
    chunks = chunk_for_llm_batch(
        batch,
        batch_size=batch_size,
        max_text_chars=settings.classify_max_text_chars,
    )

    logger.info(
        "classifier_start",
        batch_size=len(batch),
        llm_chunks=len(chunks),
        llm_batch_size=batch_size,
        prompt_mode=f"system_user_v2_{mode}",
    )

    sem = asyncio.Semaphore(settings.gemini_concurrency)

    async def process_chunk(chunk: list[dict]) -> list[dict]:
        async with sem:
            if batch_size <= 1:
                return [await classify_single(chunk[0], CLASSIFICATION_SYSTEM, usage)]
            return await classify_batch_chunk(chunk, CLASSIFICATION_SYSTEM, usage)

    nested = await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))
    results = [row for group in nested for row in group]

    processed_items = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]

    logger.info(
        "classifier_done",
        success_count=len(processed_items),
        error_count=len(errors),
        **usage.as_log_dict(),
    )

    return {"processed_items": processed_items, "errors": errors}
