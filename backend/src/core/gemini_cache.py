"""Caché explícito de contexto Gemini para clasificación de feedback."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog
from google import genai
from google.genai import types

from src.core.config import settings
from src.core.prompt_loader import load_prompt

logger = structlog.get_logger()

CLASSIFICATION_PROFILE = "classification"
_CACHE_DISPLAY_PREFIX = "feedback-classifier"


class GeminiCacheManager:
    """Gestiona caché explícito por perfil (system + few-shot)."""

    def __init__(self, client: genai.Client) -> None:
        self._client = client
        self._cache_names: dict[str, str] = {}
        self._disabled_reason: str | None = None
        self._lock = asyncio.Lock()

    async def warm_up(self, profile: str = CLASSIFICATION_PROFILE) -> None:
        """Precarga caché al arrancar el worker."""
        await self.get_cache_name(profile)

    async def get_cache_name(self, profile: str) -> str | None:
        if not settings.gemini_cache_enabled or self._disabled_reason:
            return None
        if profile in self._cache_names:
            return self._cache_names[profile]

        async with self._lock:
            if profile in self._cache_names:
                return self._cache_names[profile]
            try:
                name = await self._ensure_cache(profile)
            except Exception as exc:
                self._disabled_reason = str(exc)
                logger.warning("gemini_cache_disabled", profile=profile, error=str(exc))
                return None
            if name:
                self._cache_names[profile] = name
            return name

    def _display_name(self, profile: str) -> str:
        return f"{_CACHE_DISPLAY_PREFIX}-{profile}-{settings.gemini_cache_version}"

    async def _find_existing(self, display_name: str) -> str | None:
        pager = await self._client.aio.caches.list()
        async for cached in pager:
            if getattr(cached, "display_name", None) != display_name:
                continue
            expire_time = getattr(cached, "expire_time", None)
            if expire_time and expire_time <= datetime.now(timezone.utc):
                continue
            if cached.name:
                logger.info("gemini_cache_reused", name=cached.name, display_name=display_name)
                return cached.name
        return None

    async def _ensure_cache(self, profile: str) -> str | None:
        if profile != CLASSIFICATION_PROFILE:
            return None

        display_name = self._display_name(profile)
        existing = await self._find_existing(display_name)
        if existing:
            return existing

        system_instruction = load_prompt("classification_system_v2.md")
        fewshot = load_prompt("classification_fewshot_v1.md")
        if not system_instruction or not fewshot:
            raise RuntimeError("Prompts de clasificación no encontrados para caché")

        ttl = f"{settings.gemini_cache_ttl_seconds}s"
        config = types.CreateCachedContentConfig(
            display_name=display_name,
            system_instruction=system_instruction,
            contents=fewshot,
            ttl=ttl,
        )
        cache = await self._client.aio.caches.create(
            model=settings.gemini_model,
            config=config,
        )
        token_count = None
        usage = getattr(cache, "usage_metadata", None)
        if usage:
            token_count = getattr(usage, "total_token_count", None)

        logger.info(
            "gemini_cache_created",
            name=cache.name,
            display_name=display_name,
            ttl_seconds=settings.gemini_cache_ttl_seconds,
            cached_tokens=token_count,
        )
        return cache.name


_cache_manager: GeminiCacheManager | None = None


def get_cache_manager(client: genai.Client) -> GeminiCacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = GeminiCacheManager(client)
    return _cache_manager


def reset_cache_manager() -> None:
    """Solo para tests."""
    global _cache_manager
    _cache_manager = None
