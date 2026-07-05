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
    DATABASE_URL: str = "postgresql+asyncpg://cartoon_user:cartoon_pass@localhost:5432/cartoon_studio"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
