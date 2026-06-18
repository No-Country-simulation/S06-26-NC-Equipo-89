"""Router LLM — Gemini primario, Groq como fallback."""

from __future__ import annotations

import structlog
from pydantic import BaseModel

from src.core.config import settings
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


async def generate_json(prompt: str, schema: type[BaseModel]) -> str:
    """JSON estructurado: Gemini → Groq si falla por disponibilidad."""
    try:
        return await gemini_client.generate_json(prompt=prompt, schema=schema)
    except Exception as exc:
        if not _groq_enabled():
            raise
        if not _is_retryable(exc):
            logger.warning("llm_gemini_failed_no_fallback", error=str(exc))
            raise
        logger.warning("llm_fallback_groq_json", gemini_error=str(exc))
        return await groq_client.generate_json(prompt=prompt, schema=schema)


async def generate_text(prompt: str, temperature: float = 0.3) -> str:
    """Texto libre: Gemini → Groq si falla por disponibilidad."""
    try:
        return await gemini_client.generate_text(prompt=prompt, temperature=temperature)
    except Exception as exc:
        if not _groq_enabled():
            raise
        if not _is_retryable(exc):
            logger.warning("llm_gemini_text_failed_no_fallback", error=str(exc))
            raise
        logger.warning("llm_fallback_groq_text", gemini_error=str(exc))
        return await groq_client.generate_text(prompt=prompt, temperature=temperature)
