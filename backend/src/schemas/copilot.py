from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    since_days: int | None = Field(default=None, ge=1, le=365)


class CopilotSource(BaseModel):
    external_id: str
    texto: str
    sentimiento: str
    urgencia: str
    categorias: list[str]
    similarity: float


class CopilotResponse(BaseModel):
    answer: str
    sources: list[CopilotSource]
