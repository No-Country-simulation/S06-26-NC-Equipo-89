from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Dict, Any

class FeedbackPayload(BaseModel):
    external_id: str
    fuente: str
    texto: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra='forbid')
