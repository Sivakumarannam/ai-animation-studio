from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "AI Animation Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security — required, no default. Set SECRET_KEY in the environment.
    # A missing or placeholder value will raise a ValidationError at startup.
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"

    @field_validator("SECRET_KEY")
    @classmethod
    def require_secret_key(cls, v: str) -> str:
        insecure_defaults = {
            "change-me-in-production-use-long-random-string",
            "secret",
            "changeme",
            "",
        }
        import os
        if os.getenv("ENVIRONMENT", "development") == "production" and v in insecure_defaults:
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in production. "
                "Set the SECRET_KEY environment variable."
            )
        return v
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database — always normalized to use asyncpg driver
    DATABASE_URL: str = "postgresql+asyncpg://cartoon_user:Tiger@localhost:5432/cartoon_studio"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        """Ensure the database URL always uses the asyncpg async driver."""
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
        if not isinstance(v, str):
            return v
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                v = "postgresql+asyncpg://" + v[len(prefix):]
                break
        # asyncpg doesn't support sslmode as a query param — strip it
        parsed = urlparse(v)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params.pop("sslmode", None)
        new_query = urlencode({k: vals[0] for k, vals in params.items()})
        return urlunparse(parsed._replace(query=new_query))

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CELERY_DB: int = 1
    REDIS_CACHE_DB: int = 2

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_ASSETS: str = "assets"
    MINIO_BUCKET_VIDEOS: str = "videos"
    MINIO_BUCKET_THUMBNAILS: str = "thumbnails"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Plugin system
    ENABLED_PLUGINS: list[str] = ["telugu_family_comedy"]

    # ── Phase 3 — Story Intelligence ──────────────────────────────────────────
    # AI provider selection: "mock" | "ollama" | "openai" | "anthropic" | "gemini" | "openrouter"
    # Set to "mock" by default — no paid API required.  Switch via env var only.
    SI_AI_PROVIDER: str = "mock"

    # Quality thresholds
    SI_MIN_STORY_SCORE: float = 70.0          # Episodes below this are auto-retried
    SI_MAX_RETRIES: int = 3                    # Max auto-improvement attempts

    # Generation defaults
    SI_TARGET_EPISODE_LENGTH_SECONDS: int = 300   # 5 minutes
    SI_DEFAULT_SCENE_COUNT: int = 5
    SI_DEFAULT_EPISODES_PER_SEASON: int = 10
    SI_AI_TEMPERATURE: float = 0.7
    SI_AI_MAX_TOKENS: int = 4096
    SI_AI_MODEL: str = "mock"                 # Model name passed to the provider

    # ── Phase 4 — RAG & Knowledge Intelligence Engine ──────────────────────────
    # Embedding provider selection: "mock" | "ollama"
    EMBEDDING_PROVIDER: str = "mock"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # Vector store provider selection: "memory" | "chromadb"
    VECTOR_DB_PROVIDER: str = "memory"
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Chunking defaults
    KN_CHUNK_SIZE_TOKENS: int = 400
    KN_CHUNK_OVERLAP_TOKENS: int = 50
    KN_MAX_DOCUMENT_SIZE_MB: int = 20
    KN_DEFAULT_TOP_K: int = 5
    KN_MIN_SIMILARITY_SCORE: float = 0.15


    # ── Phase 5 — Research & Trend Intelligence Engine ────────────────────────
    # Trend provider: "mock"
    RS_TREND_PROVIDER: str = "mock"
    # Research provider: "mock"
    RS_RESEARCH_PROVIDER: str = "mock"
    # Fact verification provider: "mock"
    RS_FACT_VERIFICATION_PROVIDER: str = "mock"
    # Search provider: "mock"
    RS_SEARCH_PROVIDER: str = "mock"
    # Crawler provider: "mock"
    RS_CRAWLER_PROVIDER: str = "mock"

    # Scheduler intervals (seconds)
    RS_TREND_DISCOVERY_INTERVAL: int = 3600       # hourly
    RS_RESEARCH_REFRESH_INTERVAL: int = 21600     # 6 hours
    RS_OPPORTUNITY_REPORT_INTERVAL: int = 86400   # daily

    # Opportunity queue threshold
    RS_MIN_OPPORTUNITY_SCORE: float = 60.0

    # ── Phase 6 — AI Asset Generation Engine ─────────────────────────────────
    # Asset evaluation provider: "mock"
    AG_EVALUATION_PROVIDER: str = "mock"

    # Image provider selection: "mock" (deterministic placeholder images,
    # no external dependency) | "comfyui" (real SDXL backend, requires a
    # running ComfyUI server). Defaults to "mock" so the pipeline works
    # out of the box without a GPU/ComfyUI instance.
    AG_IMAGE_PROVIDER: str = "mock"
    COMFYUI_BASE_URL: str = "http://localhost:8188"

    # Quality threshold (0–100) — images below this score are retried
    AG_QUALITY_THRESHOLD: float = 90.0

    # Maximum retry attempts per asset
    AG_MAX_RETRIES: int = 3

    # Default image resolution
    AG_TARGET_RESOLUTION: str = "1024x1024"

    # Generation parameters defaults
    AG_DEFAULT_STEPS: int = 20
    AG_DEFAULT_CFG_SCALE: float = 7.0
    AG_DEFAULT_SAMPLER: str = "euler_a"

    # MinIO bucket for generated assets
    AG_ASSET_BUCKET: str = "assets"

    # Embedding batch size
    AG_EMBEDDING_BATCH_SIZE: int = 50

    # ── Phase 7 — Animation Engine ────────────────────────────────────────────
    AN_ANIMATION_PROVIDER: str = "mock"

    # ── Phase 8 — Voice Engine ────────────────────────────────────────────────
    VO_VOICE_PROVIDER: str = "mock"
    PIPER_BINARY: str = "piper"
    PIPER_MODELS_DIR: str = "/models/piper"

    # ── Phase 9 — Music & Sound Engine ───────────────────────────────────────
    # Music provider: "mock" (deterministic sine-tone WAV, zero-dependency) |
    # "suno" | "udio" | "musicgen" — future real providers registered here.
    MU_MUSIC_PROVIDER: str = "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
