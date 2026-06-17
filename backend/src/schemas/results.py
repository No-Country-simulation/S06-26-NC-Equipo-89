from pydantic import BaseModel, Field
from typing import List


class FeedbackClassification(BaseModel):
    sentimiento: str = Field(description="Sentimiento principal: Positivo, Negativo o Neutral")
    categorias: List[str] = Field(description="Lista de categorías aplicables")
    urgencia: str = Field(description="Nivel de urgencia: Alta, Media, Baja")
    idioma: str = Field(description="Idioma detectado en el mensaje original")
    confianza: float = Field(ge=0.0, le=1.0, description="Confianza de la clasificación entre 0 y 1")
    resumen: str = Field(description="Resumen de una línea del mensaje")
