from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    db_dsn: str = "postgresql://user:password@localhost:5432/db"  # asyncpg connection string
    gemini_api_key: str = ""
    api_key: str = "token-secreto-n8n-12345" # <-- Agregado para proteger FastAPI
    batch_size: int = 50
    gemini_concurrency: int = 10
    max_retries: int = 2
    batch_interval_minutes: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
