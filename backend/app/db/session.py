import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

# Async engine for FastAPI requests
if settings.APP_ENV == "testing" or "pytest" in sys.modules:
    async_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
else:
    engine_args = {}
    if "postgresql" in settings.DATABASE_URL:
        engine_args = {
            "pool_size": 20,
            "max_overflow": 10,
            "pool_pre_ping": True,
        }
    async_engine = create_async_engine(settings.DATABASE_URL, **engine_args)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous engine for Alembic / scripts / celery tasks
sync_engine = create_engine(settings.DATABASE_SYNC_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
