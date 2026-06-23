"""Tests de micro-batch LLM y métricas de tokens."""

from unittest.mock import AsyncMock, patch

import pytest

from src.core.llm_compact import build_batch_classify_prompt, chunk_for_llm_batch
from src.core.llm_usage import UsageStats


def test_chunk_for_llm_batch_groups_short_messages():
    items = [{"external_id": f"id-{i}", "texto": f"msg {i}"} for i in range(5)]
    chunks = chunk_for_llm_batch(items, batch_size=2, max_text_chars=300)
    assert len(chunks) == 3
    assert len(chunks[0]) == 2
    assert len(chunks[-1]) == 1


def test_chunk_for_llm_batch_isolates_long_text():
    short = {"external_id": "s1", "texto": "ok"}
    long_text = {"external_id": "l1", "texto": "x" * 400}
    chunks = chunk_for_llm_batch([short, long_text, short], batch_size=5, max_text_chars=300)
    assert len(chunks) == 3
    assert chunks[1] == [long_text]


def test_chunk_for_llm_batch_size_one_is_single_item_chunks():
    items = [{"external_id": "a", "texto": "uno"}, {"external_id": "b", "texto": "dos"}]
    chunks = chunk_for_llm_batch(items, batch_size=1, max_text_chars=300)
    assert chunks == [[items[0]], [items[1]]]


def test_build_batch_classify_prompt_compact_json():
    chunk = [
        {"external_id": "e1", "texto": "Hola"},
        {"external_id": "e2", "texto": "Chao"},
    ]
    prompt = build_batch_classify_prompt(chunk)
    assert "resultados" in prompt
    assert '"external_id":"e1"' in prompt.replace(" ", "")
    assert "Hola" in prompt


def test_usage_stats_accumulates():
    stats = UsageStats()
    stats.add({"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}, "gemini")
    stats.add({"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60}, "groq")
    log = stats.as_log_dict()
    assert log["llm_calls"] == 2
    assert log["prompt_tokens"] == 150
    assert log["total_tokens"] == 180


@pytest.mark.asyncio
async def test_classify_batch_chunk_parses_resultados():
    from src.agent.nodes.classifier import CLASSIFICATION_SYSTEM, classify_batch_chunk

    batch_json = (
        '{"resultados":['
        '{"external_id":"a","sentimiento":"Negativo","categorias":["App"],'
        '"urgencia":"Alta","idioma":"Español","confianza":0.9,"resumen":"Falla"},'
        '{"external_id":"b","sentimiento":"Positivo","categorias":["Soporte"],'
        '"urgencia":"Baja","idioma":"Español","confianza":0.8,"resumen":"Bien"}'
        "]}"
    )
    chunk = [
        {"external_id": "a", "texto": "mal"},
        {"external_id": "b", "texto": "bien"},
    ]

    with patch("src.agent.nodes.classifier.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = batch_json
        results = await classify_batch_chunk(chunk, CLASSIFICATION_SYSTEM)

    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)
    assert results[0]["classification"]["urgencia"] == "Alta"


@pytest.mark.asyncio
async def test_classify_batch_chunk_fallback_on_mismatch():
    from src.agent.nodes.classifier import CLASSIFICATION_SYSTEM, classify_batch_chunk

    chunk = [
        {"external_id": "a", "texto": "uno"},
        {"external_id": "b", "texto": "dos"},
    ]
    bad_json = (
        '{"resultados":[{"external_id":"a","sentimiento":"Neutral","categorias":[],'
        '"urgencia":"Baja","idioma":"Español","confianza":0.5,"resumen":"x"}]}'
    )

    ok_single = (
        '{"sentimiento":"Neutral","categorias":[],"urgencia":"Baja",'
        '"idioma":"Español","confianza":0.5,"resumen":"ok"}'
    )

    with patch("src.agent.nodes.classifier.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [bad_json, ok_single, ok_single]
        with patch("src.agent.nodes.classifier.settings") as mock_settings:
            mock_settings.classify_retry_attempts = 1
            results = await classify_batch_chunk(chunk, CLASSIFICATION_SYSTEM)

    assert len(results) == 2
    assert mock_gen.await_count == 3
