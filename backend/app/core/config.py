from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # PostgreSQL Database URLs (on port 5433 where our local server is running)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres@127.0.0.1:5433/bookleaf_db",
        description="Async PostgreSQL connection string",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg2://postgres@127.0.0.1:5433/bookleaf_db",
        description="Sync PostgreSQL connection string for Alembic and scripts",
    )

    # Redis & Celery
    REDIS_URL: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Redis connection URL for cache, limiter, and Celery broker",
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Celery message broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Celery result backend URL",
    )
    USE_CELERY: bool = Field(
        default=True,
        description="Flag to route async tasks through Celery (falls back to in-process async task if broker unavailable)",
    )
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable API rate limiting via slowapi",
    )

    # JWT Authentication
    JWT_SECRET: str = "supersecret_jwt_key_bookleaf_production_2026_xyz123!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Gemini AI for Support Assist
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"


    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v:
            return v
        # Normalize Render and standard PostgreSQL URLs to asyncpg driver
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg requires ssl=require instead of sslmode=require and does not accept channel_binding
        if "postgresql+asyncpg://" in v:
            v = v.replace("sslmode=require", "ssl=require")
            v = v.replace("&channel_binding=require", "")
            v = v.replace("channel_binding=require&", "")
            v = v.replace("?channel_binding=require", "")
        return v

    @field_validator("DATABASE_SYNC_URL", mode="after")
    @classmethod
    def normalize_database_sync_url(cls, v: str, info) -> str:
        if not v or "127.0.0.1" in v:
            # Check if DATABASE_URL was supplied from environment
            data = info.data
            db_url = data.get("DATABASE_URL", "")
            if db_url and "127.0.0.1" not in db_url:
                clean = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
                clean = clean.replace("postgres://", "postgresql+psycopg2://")
                clean = clean.replace("ssl=require", "sslmode=require")
                clean = clean.replace("&channel_binding=require", "")
                clean = clean.replace("channel_binding=require&", "")
                clean = clean.replace("?channel_binding=require", "")
                return clean
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v and v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
