from pydantic import BaseModel, Field
from typing import List

class FeedbackClassification(BaseModel):
    sentimiento: str = Field(description="Sentimiento principal: Positivo, Negativo o Neutral")
    categorias: List[str] = Field(description="Lista de categorías aplicables")
    urgencia: str = Field(description="Nivel de urgencia: Alta, Media, Baja")
    idioma: str = Field(description="Idioma detectado en el mensaje original")
