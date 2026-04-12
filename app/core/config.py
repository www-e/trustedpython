"""
Application configuration using Pydantic settings.

Loads configuration from environment variables and .env file with sensible defaults.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Application
    APP_NAME: str = "Game Account Marketplace"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT token signing",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/gamemarket",
        description="PostgreSQL database connection URL",
    )
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and sessions",
    )
    REDIS_EXPIRE_SECONDS: int = 3600

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # MinIO/S3
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO server endpoint")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "gamemarket"
    MINIO_REGION: str = "us-east-1"

    # Email (SMTP)
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@gamemarket.com", description="Default sender email"
    )
    SMTP_FROM_NAME: str = Field(
        default="Game Account Marketplace", description="Default sender name"
    )
    SMTP_USE_TLS: bool = True

    # Email Templates
    EMAIL_VERIFICATION_URL: str = Field(
        default="http://localhost:3000/verify-email", description="Base URL for email verification"
    )
    PASSWORD_RESET_URL: str = Field(
        default="http://localhost:3000/reset-password", description="Base URL for password reset"
    )

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".gif"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    # Fees
    PLATFORM_FEE_PERCENTAGE: float = 5.0
    MEDIATOR_FEE_PERCENTAGE: float = 2.0

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is sufficiently long in production."""
        if not cls.model_config.get("DEBUG", False) and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Cached application settings
    """
    return Settings()


# Global settings instance
settings = get_settings()
