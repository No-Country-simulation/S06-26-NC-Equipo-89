"""Tests del router LLM con fallback Groq."""

from unittest.mock import AsyncMock, patch

import pytest

from src.schemas.results import FeedbackClassification


@pytest.mark.asyncio
async def test_generate_json_falls_back_to_groq_on_503():
    from src.tools import llm_client

    with patch("src.tools.llm_client.gemini_client.generate_json", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.side_effect = Exception("503 UNAVAILABLE")
        with patch("src.tools.llm_client._groq_enabled", return_value=True):
            with patch(
                "src.tools.llm_client.groq_client.generate_json",
                new_callable=AsyncMock,
                return_value='{"sentimiento":"Neutral","categorias":[],"urgencia":"Baja","idioma":"Español","confianza":0.5,"resumen":"ok"}',
            ) as mock_groq:
                result = await llm_client.generate_json("test", FeedbackClassification)
                assert "Neutral" in result
                mock_groq.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_json_no_fallback_without_groq_key():
    from src.tools import llm_client

    with patch("src.tools.llm_client.gemini_client.generate_json", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.side_effect = Exception("503 UNAVAILABLE")
        with patch("src.tools.llm_client._groq_enabled", return_value=False):
            with pytest.raises(Exception, match="503"):
                await llm_client.generate_json("test", FeedbackClassification)
