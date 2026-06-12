"""Application configuration (TECH_STACK_DECISION.md service endpoints)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_name: str = "AI Multi-Agent Platform API"
    environment: str = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Security (JWT / OIDC) ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- PostgreSQL (async) ---
    postgres_dsn: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform"
    )

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Qdrant (vector DB) ---
    qdrant_url: str = "http://localhost:6333"

    # --- MinIO / S3 object storage ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    # --- Kafka event bus ---
    kafka_bootstrap_servers: str = "localhost:9092"

    # --- LLM / embeddings ---
    llm_base_url: str = "https://api.anthropic.com"
    llm_api_key: str = ""

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are read from the environment once."""
    return Settings()
