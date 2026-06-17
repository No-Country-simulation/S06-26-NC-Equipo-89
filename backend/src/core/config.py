from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    db_dsn: str = "postgresql://user:password@localhost:5432/db"  # asyncpg connection string
    gemini_api_key: str = ""
    cohere_api_key: str = ""
    api_key: str = "token-secreto-n8n-12345" # <-- Agregado para proteger FastAPI
    batch_size: int = 50
    gemini_concurrency: int = 10
    max_retries: int = 2
    batch_interval_minutes: int = 5
    embed_batch_size: int = 50
    embed_max_per_run: int = 500
    embed_job_sleep_seconds: int = 2
    copilot_match_count: int = 10
    copilot_default_since_days: int = 7

    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_ENV), str(_BACKEND_ENV), ".env"),
        extra="ignore",
    )

settings = Settings()
