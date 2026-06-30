"""Corrección y confirmación humana de clasificaciones."""

from __future__ import annotations

import json

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api.deps import rate_limit_ingest, verify_api_key
from src.schemas.results import FeedbackClassification
from src.tools.supabase_client import get_db

logger = structlog.get_logger()
router = APIRouter(prefix="/classifications", tags=["classifications"])


class ClassificationConfirm(BaseModel):
    """Confirma la clasificación existente sin cambios."""

    motivo: str = Field(default="confirmacion_humana")


class ClassificationCorrection(FeedbackClassification):
    """Corrección de campos clasificados."""

    motivo: str = Field(default="correccion_humana")


@router.patch("/{external_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_classification(
    external_id: str,
    payload: ClassificationConfirm,
    request: Request,
    _=Depends(verify_api_key),
    __=Depends(rate_limit_ingest),
):
    """Marca una clasificación como confirmada por un humano."""
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT fc.sentimiento, fc.urgencia, fc.idioma, fc.categorias,
                   fc.confianza, fc.resumen, fr.texto
            FROM feedback_clasificado fc
            JOIN feedback_raw fr ON fr.external_id = fc.external_id
            WHERE fc.external_id = $1
            """,
            external_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Clasificación no encontrada")

        original = {
            "sentimiento": row["sentimiento"],
            "urgencia": row["urgencia"],
            "idioma": row["idioma"],
            "categorias": json.loads(row["categorias"])
            if isinstance(row["categorias"], str)
            else row["categorias"],
            "confianza": row["confianza"],
            "resumen": row["resumen"],
        }

        await conn.execute(
            """
            UPDATE feedback_clasificado
            SET requiere_revision = FALSE, revision_estado = 'confirmado'
            WHERE external_id = $1
            """,
            external_id,
        )
        await conn.execute(
            """
            INSERT INTO feedback_correcciones
                (external_id, texto_original, clasificacion_original,
                 clasificacion_corregida, motivo)
            VALUES ($1, $2, $3, $4, $5)
            """,
            external_id,
            row["texto"],
            json.dumps(original),
            json.dumps(original),
            payload.motivo,
        )

    logger.info("classification_confirmed", external_id=external_id)
    return {"status": "confirmed", "external_id": external_id}


@router.patch("/{external_id}", status_code=status.HTTP_200_OK)
async def correct_classification(
    external_id: str,
    payload: ClassificationCorrection,
    request: Request,
    _=Depends(verify_api_key),
    __=Depends(rate_limit_ingest),
):
    """Corrige una clasificación y registra el aprendizaje humano."""
    pool = await get_db()
    corrected = payload.model_dump(exclude={"motivo"})
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT fc.sentimiento, fc.urgencia, fc.idioma, fc.categorias,
                   fc.confianza, fc.resumen, fr.texto
            FROM feedback_clasificado fc
            JOIN feedback_raw fr ON fr.external_id = fc.external_id
            WHERE fc.external_id = $1
            """,
            external_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Clasificación no encontrada")

        original = {
            "sentimiento": row["sentimiento"],
            "urgencia": row["urgencia"],
            "idioma": row["idioma"],
            "categorias": json.loads(row["categorias"])
            if isinstance(row["categorias"], str)
            else row["categorias"],
            "confianza": row["confianza"],
            "resumen": row["resumen"],
        }

        await conn.execute(
            """
            UPDATE feedback_clasificado
            SET sentimiento = $2, urgencia = $3, idioma = $4, categorias = $5,
                confianza = $6, resumen = $7,
                requiere_revision = FALSE, revision_estado = 'corregido'
            WHERE external_id = $1
            """,
            external_id,
            corrected["sentimiento"],
            corrected["urgencia"],
            corrected["idioma"],
            json.dumps(corrected.get("categorias", [])),
            corrected["confianza"],
            corrected["resumen"],
        )
        await conn.execute(
            """
            INSERT INTO feedback_correcciones
                (external_id, texto_original, clasificacion_original,
                 clasificacion_corregida, motivo)
            VALUES ($1, $2, $3, $4, $5)
            """,
            external_id,
            row["texto"],
            json.dumps(original),
            json.dumps(corrected),
            payload.motivo,
        )

    logger.info("classification_corrected", external_id=external_id)
    return {"status": "corrected", "external_id": external_id, "classification": corrected}
