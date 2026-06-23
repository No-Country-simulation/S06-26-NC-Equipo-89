from pydantic import BaseModel, Field
from typing import List


class FeedbackClassification(BaseModel):
    sentimiento: str = Field(description="Sentimiento principal: Positivo, Negativo o Neutral")
    categorias: List[str] = Field(description="Lista de categorías aplicables")
    urgencia: str = Field(description="Nivel de urgencia: Alta, Media, Baja")
    idioma: str = Field(description="Idioma detectado en el mensaje original")
    confianza: float = Field(ge=0.0, le=1.0, description="Confianza de la clasificación entre 0 y 1")
    resumen: str = Field(description="Resumen de una línea del mensaje")


class BatchClassifiedItem(FeedbackClassification):
    external_id: str = Field(description="ID del mensaje clasificado")


class BatchClassificationResult(BaseModel):
    resultados: List[BatchClassifiedItem] = Field(
        description="Un resultado por cada external_id del lote de entrada"
    )
