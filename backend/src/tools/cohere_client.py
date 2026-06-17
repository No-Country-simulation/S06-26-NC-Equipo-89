import structlog
import cohere
from src.core.config import settings

logger = structlog.get_logger()

EMBED_MODEL = "embed-multilingual-v3.0"


class CohereClient:
    def __init__(self) -> None:
        self._client = cohere.AsyncClientV2(api_key=settings.cohere_api_key)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para indexación de documentos (feedback)."""
        if not texts:
            return []
        try:
            response = await self._client.embed(
                texts=texts,
                model=EMBED_MODEL,
                input_type="search_document",
                embedding_types=["float"],
            )
            logger.info("cohere_embed_batch_success", count=len(texts))
            return response.embeddings.float_
        except Exception as e:
            logger.error("cohere_embed_batch_failed", error=str(e), count=len(texts))
            raise

    async def embed_query(self, text: str) -> list[float]:
        """Genera embedding para una pregunta del Copilot."""
        try:
            response = await self._client.embed(
                texts=[text],
                model=EMBED_MODEL,
                input_type="search_query",
                embedding_types=["float"],
            )
            logger.info("cohere_embed_query_success")
            return response.embeddings.float_[0]
        except Exception as e:
            logger.error("cohere_embed_query_failed", error=str(e))
            raise


cohere_client = CohereClient()
