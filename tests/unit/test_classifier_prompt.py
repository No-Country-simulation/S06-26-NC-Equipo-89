"""Tests del clasificador con prompt system/user optimizado."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agent.nodes.classifier import CLASSIFICATION_SYSTEM, classify_single


@pytest.mark.asyncio
async def test_classify_single_passes_system_instruction():
    with patch("src.agent.nodes.classifier.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (
            '{"sentimiento":"Negativo","categorias":["App"],"urgencia":"Alta",'
            '"idioma":"Español","confianza":0.9,"resumen":"Falla"}'
        )
        result = await classify_single(
            {"external_id": "t-1", "texto": "La app no abre"},
            CLASSIFICATION_SYSTEM,
        )

    assert result["status"] == "success"
    assert result["classification"]["urgencia"] == "Alta"
    mock_gen.assert_awaited_once()
    call_kwargs = mock_gen.await_args.kwargs
    assert call_kwargs["prompt"] == "La app no abre"
    assert call_kwargs["system_instruction"] == CLASSIFICATION_SYSTEM
    assert "urgencia" in call_kwargs["system_instruction"]


@pytest.mark.asyncio
async def test_classification_system_prompt_is_compact():
    """El system prompt v2 debe ser más corto que el template monolítico legacy."""
    from src.core.prompt_loader import load_prompt

    legacy = load_prompt("classification_v1.md")
    assert len(CLASSIFICATION_SYSTEM) < len(legacy)
