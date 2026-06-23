import structlog
from google import genai
from google.genai import types

from src.core.config import settings
from src.core.gemini_cache import CLASSIFICATION_PROFILE, get_cache_manager

logger = structlog.get_logger()


def _extract_usage(response) -> dict[str, int]:
    meta = getattr(response, "usage_metadata", None)
    if not meta:
        return {}
    prompt = int(getattr(meta, "prompt_token_count", 0) or 0)
    completion = int(getattr(meta, "candidates_token_count", 0) or 0)
    total = int(getattr(meta, "total_token_count", 0) or 0)
    cached = int(getattr(meta, "cached_content_token_count", 0) or 0)
    if not total:
        total = prompt + completion
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_content_token_count": cached,
    }


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self._cache_manager = get_cache_manager(self.client)

    async def warm_classification_cache(self) -> None:
        """Precarga caché explícito (Fase B)."""
        if settings.gemini_cache_enabled:
            await self._cache_manager.warm_up(CLASSIFICATION_PROFILE)

    async def generate_json(
        self,
        prompt: str,
        schema: type,
        *,
        system_instruction: str | None = None,
        cache_profile: str | None = None,
    ) -> tuple[str, dict[str, int]]:
        """Genera JSON estructurado; retorna (texto, usage)."""
        try:
            config_kwargs: dict = {
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.1,
            }

            cache_name = None
            if system_instruction and cache_profile:
                cache_name = await self._cache_manager.get_cache_name(cache_profile)

            if cache_name:
                config_kwargs["cached_content"] = cache_name
            elif system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            usage = _extract_usage(response)
            logger.info(
                "gemini_call_success",
                has_cache=bool(cache_name),
                has_system=bool(system_instruction and not cache_name),
                **usage,
            )
            return response.text, usage
        except Exception as e:
            logger.error("gemini_call_failed", error=str(e))
            raise

    async def generate_text(self, prompt: str, temperature: float = 0.3) -> tuple[str, dict[str, int]]:
        """Genera texto libre; retorna (texto, usage)."""
        try:
            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            usage = _extract_usage(response)
            logger.info("gemini_text_success", **usage)
            return response.text or "", usage
        except Exception as e:
            logger.error("gemini_text_failed", error=str(e))
            raise


gemini_client = GeminiClient()
