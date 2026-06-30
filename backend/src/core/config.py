from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    env: str = "development"
    db_dsn: str = "postgresql://user:password@localhost:5432/db"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_cache_enabled: bool = True
    gemini_cache_ttl_seconds: int = 3600
    gemini_cache_version: str = "v3-taxonomia1"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    cohere_api_key: str = ""
    api_key: str = ""
    min_api_key_length: int = 32
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
    stuck_processing_minutes: int = 30
    cors_origins: str = ""
    rate_limit_ingest_per_minute: int = 60
    rate_limit_copilot_per_minute: int = 30
    log_pii: bool = True
    confidence_review_threshold: float = 0.7
    alert_urgencia_alta_threshold: int = 5
    alert_negativo_spike_pct: float = 50.0
    consistency_check_interval_days: int = 7
    consistency_check_runs: int = 3
    consistency_check_stability_threshold: float = 0.70
    recurring_topics_interval_days: int = 1   # 0 = desactivado
    recurring_topics_period_days: int = 7     # ventana de análisis histórico

    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_ENV), str(_BACKEND_ENV), ".env"),
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.is_production:
            if len(self.api_key) < self.min_api_key_length:
                raise ValueError(
                    f"API_KEY debe tener al menos {self.min_api_key_length} caracteres en producción"
                )
            self.log_pii = False
        return self


settings = Settings()
