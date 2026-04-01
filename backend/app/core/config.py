"""
Application Configuration
"""
import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Project Info
    PROJECT_NAME: str = "Link1Die API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A production-ready FastAPI application"

    # API Configuration
    API_PORT: int = 8000
    DEBUG: bool = False

    # Database - support SQLite for development
    DATABASE_URL: str = "sqlite:///./link1die.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # JWT Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production-minimum-32-char"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SHARE_LINK_EXPIRE_MINUTES: int = 5

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = True

    # File Storage
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: list[str] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "txt", "xlsx", "csv"]
    )
    UPLOAD_DIR: str = "./uploads"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vercel Blob (optional)
    BLOB_ACCESS: str = "private"

    # Public base URL for generating share links (e.g. https://link1die.xyz)
    PUBLIC_BASE_URL: str | None = None

    # Desktop packaging (optional)
    WEB_DIST_DIR: str | None = None

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> bool:
        """Treat common build-mode strings as valid booleans."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip().lower()
            truthy_values = {"1", "true", "yes", "on", "debug", "dev", "development"}
            falsy_values = {"0", "false", "no", "off", "release", "prod", "production"}
            if normalized in truthy_values:
                return True
            if normalized in falsy_values:
                return False
        return bool(value)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def default_database_url_from_vercel(cls, value: object) -> object:
        """If DATABASE_URL is not set, fall back to Vercel Postgres env vars."""
        if isinstance(value, str) and value.strip():
            return value
        from os import environ

        for key in ("POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING"):
            candidate = environ.get(key)
            if candidate:
                return candidate
        return value

    @field_validator("CORS_ORIGINS", "ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_list_setting(cls, value: object) -> object:
        """Allow JSON arrays or comma-separated strings in env vars."""
        if not isinstance(value, str):
            return value

        stripped = value.strip()
        if not stripped:
            return []

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [item.strip() for item in stripped.split(",") if item.strip()]

        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]


settings = Settings()
