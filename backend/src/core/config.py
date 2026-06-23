from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    db_dsn: str = "postgresql://user:password@localhost:5432/db"  # asyncpg connection string
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_cache_enabled: bool = True
    gemini_cache_ttl_seconds: int = 3600
    gemini_cache_version: str = "v2-fewshot1"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    cohere_api_key: str = ""
    api_key: str = ""
    batch_size: int = 50
    gemini_concurrency: int = 3
    max_retries: int = 4
    classify_retry_attempts: int = 3
    classify_retry_base_seconds: float = 2.0
    classify_llm_batch_size: int = 8
    classify_max_text_chars: int = 300
    batch_interval_minutes: int = 5
    embed_batch_size: int = 50
    embed_max_per_run: int = 500
    embed_job_sleep_seconds: int = 2
    copilot_match_count: int = 10

    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_ENV), str(_BACKEND_ENV), ".env"),
        extra="ignore",
    )

settings = Settings()
