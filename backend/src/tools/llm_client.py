"""Router LLM — Gemini primario, Groq como fallback."""

from __future__ import annotations

import structlog
from pydantic import BaseModel

from src.core.config import settings
from src.core.llm_usage import UsageStats, merge_usage_stats
from src.tools.gemini_client import gemini_client
from src.tools.groq_client import groq_client

logger = structlog.get_logger()


def _groq_enabled() -> bool:
    return bool(settings.groq_api_key and groq_client.available)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in ("503", "429", "unavailable", "timeout", "overloaded", "rate")
    )


async def generate_json(
    prompt: str,
    schema: type[BaseModel],
    *,
    system_instruction: str | None = None,
    usage_stats: UsageStats | None = None,
    cache_profile: str | None = None,
) -> str:
    """JSON estructurado: Gemini → Groq si falla por disponibilidad."""
    if cache_profile is None and system_instruction:
        from src.core.gemini_cache import CLASSIFICATION_PROFILE

        cache_profile = CLASSIFICATION_PROFILE

    try:
        text, usage = await gemini_client.generate_json(
            prompt=prompt,
            schema=schema,
            system_instruction=system_instruction,
            cache_profile=cache_profile,
        )
        merge_usage_stats(usage_stats, usage, "gemini")
        return text
    except Exception as exc:
        if not _groq_enabled():
            raise
        if not _is_retryable(exc):
            logger.warning("llm_gemini_failed_no_fallback", error=str(exc))
            raise
        logger.warning("llm_fallback_groq_json", gemini_error=str(exc))
        text, usage = await groq_client.generate_json(
            prompt=prompt,
            schema=schema,
            system_instruction=system_instruction,
        )
        merge_usage_stats(usage_stats, usage, "groq")
        return text


async def generate_text(prompt: str, temperature: float = 0.3) -> str:
    """Texto libre: Gemini → Groq si falla por disponibilidad."""
    try:
        text, usage = await gemini_client.generate_text(prompt=prompt, temperature=temperature)
        logger.info("llm_token_usage", provider="gemini", **usage)
        return text
    except Exception as exc:
        if not _groq_enabled():
            raise
        if not _is_retryable(exc):
            logger.warning("llm_gemini_text_failed_no_fallback", error=str(exc))
            raise
        logger.warning("llm_fallback_groq_text", gemini_error=str(exc))
        text, usage = await groq_client.generate_text(prompt=prompt, temperature=temperature)
        logger.info("llm_token_usage", provider="groq", **usage)
        return text
