"""Cliente Groq — fallback cuando Gemini no está disponible."""

from __future__ import annotations

import json
import structlog
from groq import AsyncGroq
from pydantic import BaseModel

from src.core.config import settings

logger = structlog.get_logger()


def _extract_usage(response) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if not usage:
        return {}
    return {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


class GroqClient:
    def __init__(self) -> None:
        self._client: AsyncGroq | None = None
        if settings.groq_api_key:
            self._client = AsyncGroq(api_key=settings.groq_api_key)

    @property
    def available(self) -> bool:
        return self._client is not None

    async def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system_instruction: str | None = None,
    ) -> tuple[str, dict[str, int]]:
        if not self._client:
            raise RuntimeError("GROQ_API_KEY no configurada")

        schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        user_content = prompt
        if not system_instruction:
            user_content = (
                f"{prompt}\n\n"
                "Responde ÚNICAMENTE con un objeto JSON válido (sin markdown) "
                f"que cumpla este schema:\n{schema_hint}"
            )

        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"{user_content}\n\n"
                    "Responde ÚNICAMENTE con JSON válido (sin markdown) "
                    f"según schema:\n{schema_hint}"
                ),
            }
        )

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        usage = _extract_usage(response)
        logger.info("groq_call_success", model=settings.groq_model, **usage)
        return text, usage

    async def generate_text(self, prompt: str, temperature: float = 0.3) -> tuple[str, dict[str, int]]:
        if not self._client:
            raise RuntimeError("GROQ_API_KEY no configurada")

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        usage = _extract_usage(response)
        logger.info("groq_text_success", model=settings.groq_model, **usage)
        return text, usage


groq_client = GroqClient()
