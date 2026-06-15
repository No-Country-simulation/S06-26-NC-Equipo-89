import structlog
from google import genai
from src.core.config import settings

logger = structlog.get_logger()

class GeminiClient:
    def __init__(self):
        # Asegurarse de tener configurado gemini_api_key
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def generate_json(self, prompt: str, schema: type) -> str:
        """
        Genera contenido estructurado (JSON) usando Gemini Flash-Lite.
        """
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1
                )
            )
            logger.info("gemini_call_success")
            return response.text
        except Exception as e:
            logger.error("gemini_call_failed", error=str(e))
            raise

gemini_client = GeminiClient()
