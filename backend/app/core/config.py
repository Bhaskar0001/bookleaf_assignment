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
        description="Sync PostgreSQL connection string for Alembic/Celery",
    )

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET: str = "supersecret_jwt_key_bookleaf_production_2026_xyz123!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # AI Provider Boundary (Server-side only)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

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
