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
    documents_bucket: str = "documents"

    # --- OCR (FR-006) ---
    # Tesseract language packs, '+'-joined (e.g. "tuk+eng+rus").
    ocr_languages: str = "tuk+eng+rus"
    # If a PDF yields fewer than this many characters via the text layer, treat
    # it as scanned and fall back to OCR.
    ocr_pdf_min_chars: int = 32
    # DPI used when rasterising PDF pages for OCR.
    ocr_pdf_dpi: int = 200

    # --- Knowledge layer: chunking (CH-002) ---
    # Token budgets are approximate; tokens are estimated as chars / chars_per_token.
    chunk_target_tokens: int = 512
    chunk_overlap_tokens: int = 64
    chunk_max_tokens: int = 1024
    chunk_chars_per_token: int = 4

    # --- Knowledge layer: embeddings (EM-001/EM-002) ---
    # Model + dimension are pinned per deployment; one collection = one model/dim.
    # The default `hashing-v1` provider is fully offline (no API/GPU); swap for
    # Voyage AI / BGE-M3 by registering another EmbeddingProvider.
    embedding_model: str = "hashing-v1"
    embedding_dim: int = 256

    # --- Knowledge layer: Qdrant collection ---
    qdrant_documents_collection: str = "documents"
    retrieval_top_k: int = 20

    # --- Workflow engine (Task 13) ---
    # In-process MVP retries immediately; the spec's 30s/2m/10m backoff (EH-001)
    # applies once dispatch is event-driven over Kafka.
    workflow_max_attempts: int = 2
    workflow_step_max_tokens: int = 400

    # --- Kafka event bus ---
    kafka_bootstrap_servers: str = "localhost:9092"

    # --- LLM / embeddings ---
    llm_base_url: str = "https://api.anthropic.com"
    llm_api_key: str = ""

    # --- LLM provider (MP-001): all model calls go through one interface ---
    # Default provider is local Ollama proxying the gemma4:31b-cloud model.
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:31b-cloud"
    llm_timeout_seconds: int = 120
    # Model routing tiers (MR-002, data-driven). All map to the Ollama model
    # for this deployment; swap per tier when more providers are registered.
    llm_model_reasoning: str = "gemma4:31b-cloud"
    llm_model_general: str = "gemma4:31b-cloud"
    llm_model_light: str = "gemma4:31b-cloud"

    # --- Memory layer (Faza 6 / AG-009, ME-001..ME-002) ---
    # Session memory lives in Redis. Retention matches DATABASE_DESIGN (30 days).
    session_memory_ttl_seconds: int = 60 * 60 * 24 * 30
    # Context compression (ME-002): when a session exceeds max_turns, the oldest
    # turns are folded into a running summary, keeping only the most recent.
    session_memory_max_turns: int = 20
    session_memory_recent_turns: int = 8
    # Long-term memory semantic recall reuses the embedding model in its own
    # Qdrant collection (one collection = one model/dim, per EM-002).
    qdrant_memory_collection: str = "memory"
    memory_recall_top_k: int = 5

    # --- Computer Use / Execution Agent (Faza 7 / AG-008, FR-015, SB-001..008) ---
    # Every Execution Agent task runs inside a sandbox. The scratch dir is the
    # only writable storage (SB-002); file actions are confined to it.
    execution_scratch_dir: str = "/tmp/agent-sandbox"
    # Default-deny egress (SB-008): browser actions may only reach these hosts.
    execution_egress_allowlist: list[str] = ["example.com", "www.example.com"]
    # Capability grant (SB-003): only these executables may be run.
    execution_command_allowlist: list[str] = ["echo", "cat", "ls", "true"]
    # Resource limits (SB-006).
    execution_process_timeout_seconds: float = 10.0
    execution_max_output_chars: int = 10_000

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are read from the environment once."""
    return Settings()
