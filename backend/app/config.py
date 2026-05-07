from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "LogLens"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://loglens:loglens@localhost:5432/loglens"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "loglens-uploads"

    # Anthropic / custom LLM proxy
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5"
    llm_max_tokens: int = 8192
    # Özel API base URL — boşsa resmi Anthropic API kullanılır
    anthropic_base_url: str = ""

    # Clerk
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    # File Upload
    max_upload_size_bytes: int = 500 * 1024 * 1024  # 500MB


@lru_cache
def get_settings() -> Settings:
    return Settings()
