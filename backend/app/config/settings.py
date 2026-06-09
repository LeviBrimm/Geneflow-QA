from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GeneFlow QA Platform"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://geneflow:geneflow@localhost:5432/geneflow"
    auth_secret: str = "change-me-in-production"
    access_token_minutes: int = 60 * 24
    ai_mode: str = "mock"
    openai_api_key: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    redis_url: str = "redis://localhost:6379/0"
    analysis_queue_name: str = "analysis"
    analysis_queue_mode: str = "rq"
    external_reference_mode: str = "mock"
    external_reference_base_url: str = "https://rest.ensembl.org"
    external_reference_timeout_seconds: float = 3.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
