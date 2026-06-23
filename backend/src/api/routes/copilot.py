import json
import structlog
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.deps import rate_limit_copilot, verify_api_key
from src.core.config import settings
from src.core.pgvector import vector_to_pg
from src.schemas.copilot import CopilotRequest, CopilotResponse, CopilotSource
from src.tools.cohere_client import cohere_client
from src.tools.llm_client import generate_text
from src.tools.supabase_client import get_db

logger = structlog.get_logger()
router = APIRouter()

_ROOT = Path(__file__).resolve().parents[4]
PROMPT_PATH = _ROOT / "prompts" / "copilot_v1.md"


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
    request: Request,
    _=Depends(verify_api_key),
    __=Depends(rate_limit_copilot),
) -> CopilotResponse:
    """Responde preguntas del analista usando RAG sobre feedback indexado."""
    question = payload.question.strip()
    # None = todo el feedback indexado; since_days opcional acota por fecha
    since_date = None
    if payload.since_days is not None:
        since_date = datetime.now(timezone.utc) - timedelta(days=payload.since_days)

    try:
        query_embedding = await cohere_client.embed_query(question)
        embedding_pg = vector_to_pg(query_embedding)

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
                    "No encontré feedback indexado para tu consulta. "
                    "Es posible que el job de indexación aún no haya procesado los mensajes nuevos. "
                    "Intenta de nuevo más tarde o verifica que existan embeddings en feedback_clasificado."
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
        answer = await generate_text(prompt)

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
