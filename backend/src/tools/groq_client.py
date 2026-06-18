"""Cliente Groq — fallback cuando Gemini no está disponible."""

from __future__ import annotations

import json
import structlog
from groq import AsyncGroq
from pydantic import BaseModel

from src.core.config import settings

logger = structlog.get_logger()


class GroqClient:
    def __init__(self) -> None:
        self._client: AsyncGroq | None = None
        if settings.groq_api_key:
            self._client = AsyncGroq(api_key=settings.groq_api_key)

    @property
    def available(self) -> bool:
        return self._client is not None

    async def generate_json(self, prompt: str, schema: type[BaseModel]) -> str:
        if not self._client:
            raise RuntimeError("GROQ_API_KEY no configurada")

        schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        full_prompt = (
            f"{prompt}\n\n"
            "Responde ÚNICAMENTE con un objeto JSON válido (sin markdown) "
            f"que cumpla este schema:\n{schema_hint}"
        )

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        logger.info("groq_call_success", model=settings.groq_model)
        return text

    async def generate_text(self, prompt: str, temperature: float = 0.3) -> str:
        if not self._client:
            raise RuntimeError("GROQ_API_KEY no configurada")

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        logger.info("groq_text_success", model=settings.groq_model)
        return text


groq_client = GroqClient()
