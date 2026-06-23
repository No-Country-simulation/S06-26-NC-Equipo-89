"""Tests de caché explícito Gemini (Fase B)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.gemini_cache import CLASSIFICATION_PROFILE, GeminiCacheManager, reset_cache_manager
from src.core.prompt_loader import load_prompt


def test_fewshot_prompt_meets_minimum_size():
    """Few-shot debe superar ~2k tokens estimados para caché explícita."""
    fewshot = load_prompt("classification_fewshot_v1.md")
    system = load_prompt("classification_system_v2.md")
    combined = system + fewshot
    assert len(combined) >= 6000, "Contenido cacheable insuficiente para umbral Gemini"


@pytest.mark.asyncio
async def test_cache_manager_reuses_existing_by_display_name():
    reset_cache_manager()
    mock_client = MagicMock()
    existing = MagicMock()
    existing.display_name = "feedback-classifier-classification-v2-fewshot1"
    existing.name = "cachedContents/abc123"
    existing.expire_time = None

    async def _aiter():
        yield existing

    pager = MagicMock()
    pager.__aiter__ = lambda self: _aiter()
    mock_client.aio.caches.list = AsyncMock(return_value=pager)

    manager = GeminiCacheManager(mock_client)
    with patch("src.core.gemini_cache.settings") as mock_settings:
        mock_settings.gemini_cache_enabled = True
        mock_settings.gemini_cache_version = "v2-fewshot1"
        name = await manager.get_cache_name(CLASSIFICATION_PROFILE)

    assert name == "cachedContents/abc123"
    mock_client.aio.caches.create.assert_not_called()


@pytest.mark.asyncio
async def test_cache_manager_creates_when_missing():
    reset_cache_manager()
    mock_client = MagicMock()

    class _EmptyAsyncIter:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    pager = _EmptyAsyncIter()
    mock_client.aio.caches.list = AsyncMock(return_value=pager)

    created = MagicMock()
    created.name = "cachedContents/new"
    created.usage_metadata = MagicMock(total_token_count=2500)
    mock_client.aio.caches.create = AsyncMock(return_value=created)

    manager = GeminiCacheManager(mock_client)
    with patch("src.core.gemini_cache.settings") as mock_settings:
        mock_settings.gemini_cache_enabled = True
        mock_settings.gemini_cache_version = "v2-fewshot1"
        mock_settings.gemini_cache_ttl_seconds = 3600
        mock_settings.gemini_model = "gemini-2.5-flash-lite"
        name = await manager.get_cache_name(CLASSIFICATION_PROFILE)

    assert name == "cachedContents/new"
    mock_client.aio.caches.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_client_uses_cached_content_when_available():
    from src.schemas.results import FeedbackClassification
    from src.tools.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    client.client = MagicMock()
    client._cache_manager = MagicMock()
    client._cache_manager.get_cache_name = AsyncMock(return_value="cachedContents/test")

    response = MagicMock()
    response.text = '{"sentimiento":"Neutral","categorias":[],"urgencia":"Baja","idioma":"Español","confianza":0.5,"resumen":"ok"}'
    response.usage_metadata = MagicMock(
        prompt_token_count=100,
        candidates_token_count=20,
        total_token_count=120,
        cached_content_token_count=2000,
    )
    client.client.aio.models.generate_content = AsyncMock(return_value=response)

    with patch("src.tools.gemini_client.settings") as mock_settings:
        mock_settings.gemini_model = "gemini-2.5-flash-lite"
        text, usage = await client.generate_json(
            prompt="Hola",
            schema=FeedbackClassification,
            system_instruction="reglas",
            cache_profile=CLASSIFICATION_PROFILE,
        )

    assert "Neutral" in text
    assert usage["cached_content_token_count"] == 2000
    call_kwargs = client.client.aio.models.generate_content.await_args.kwargs
    config = call_kwargs["config"]
    assert config.cached_content == "cachedContents/test"
    assert not getattr(config, "system_instruction", None)
