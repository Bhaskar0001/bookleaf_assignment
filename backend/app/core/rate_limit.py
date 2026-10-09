import sys
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings
from app.core.logging import logger


def create_limiter() -> Limiter:
    """
    Initializes SlowAPI Limiter.
    Uses Redis storage if REDIS_URL is reachable, with automatic fallback to in-memory storage.
    Automatically disables during unit/integration tests to prevent mock client throttling.
    """
    is_testing = settings.APP_ENV == "testing" or "pytest" in sys.modules
    enabled = settings.RATE_LIMIT_ENABLED and not is_testing
    storage_uri = "memory://"

    if settings.REDIS_URL and enabled:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5)
            r.ping()
            storage_uri = settings.REDIS_URL
            logger.info(f"Rate Limiter connected to Redis backend: {settings.REDIS_URL}")
        except Exception:
            logger.info("Redis not available; Rate Limiter using in-memory backend.")
            storage_uri = "memory://"

    return Limiter(
        key_func=get_remote_address,
        default_limits=["120/minute"],
        storage_uri=storage_uri,
        enabled=enabled,
        headers_enabled=False,
    )


limiter = create_limiter()
