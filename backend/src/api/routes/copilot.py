import json
import structlog
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import settings
from src.schemas.copilot import CopilotRequest, CopilotResponse, CopilotSource
from src.tools.cohere_client import cohere_client
from src.tools.gemini_client import gemini_client
from src.tools.supabase_client import get_db

logger = structlog.get_logger()
router = APIRouter()

api_key_header = APIKeyHeader(name="X-API-Key")
PROMPT_PATH = Path("prompts/copilot_v1.md")


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != settings.api_key:
        logger.warning("copilot_auth_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


def _vector_to_pg(vector: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


def _load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Contexto: {contexto}\nPregunta: {pregunta}"


def _parse_categorias(categorias) -> list[str]:
    if isinstance(categorias, list):
        return categorias
    if isinstance(categorias, str):
        return json.loads(categorias)
    return []


def _build_context(sources: list[dict]) -> str:
    blocks = []
    for i, src in enumerate(sources, start=1):
        cat_str = ", ".join(_parse_categorias(src.get("categorias"))) or "sin categoría"
        blocks.append(
            f"[{i}] Sentimiento: {src['sentimiento']} | Urgencia: {src['urgencia']} | "
            f"Categorías: {cat_str}\nTexto: {src['texto']}"
        )
    return "\n\n".join(blocks)


@router.post("/ask", response_model=CopilotResponse)
async def ask_copilot(
    payload: CopilotRequest,
    _=Depends(verify_api_key),
) -> CopilotResponse:
    """Responde preguntas del analista usando RAG sobre feedback indexado."""
    question = payload.question.strip()
    since_days = payload.since_days or settings.copilot_default_since_days
    since_date = datetime.now(timezone.utc) - timedelta(days=since_days)

    try:
        query_embedding = await cohere_client.embed_query(question)
        embedding_pg = _vector_to_pg(query_embedding)

        pool = await get_db()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT external_id, texto, sentimiento, urgencia, categorias, similarity
                FROM match_feedback($1::vector, $2, $3)
                """,
                embedding_pg,
                settings.copilot_match_count,
                since_date,
            )

        if not rows:
            return CopilotResponse(
                answer=(
                    "No encontré feedback indexado para tu consulta en el período seleccionado. "
                    "Es posible que el job de indexación aún no haya procesado los mensajes nuevos. "
                    "Intenta ampliar el rango de días o espera a la próxima corrida de indexación."
                ),
                sources=[],
            )

        sources = [
            CopilotSource(
                external_id=row["external_id"],
                texto=row["texto"],
                sentimiento=row["sentimiento"],
                urgencia=row["urgencia"],
                categorias=_parse_categorias(row["categorias"]),
                similarity=round(float(row["similarity"]), 4),
            )
            for row in rows
        ]

        template = _load_prompt_template()
        prompt = template.format(
            contexto=_build_context([dict(r) for r in rows]),
            pregunta=question,
        )
        answer = await gemini_client.generate_text(prompt)

        logger.info("copilot_ask_success", sources_count=len(sources))
        return CopilotResponse(answer=answer, sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("copilot_ask_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la consulta del Copilot",
        )
