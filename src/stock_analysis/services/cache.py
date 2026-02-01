"""Cache service."""

from asyncio import Lock
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from redis.asyncio import ConnectionPool, Redis

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


_redis_lock = Lock()

settings: Settings = get_settings()
pool = ConnectionPool(host=settings.redis_host, port=settings.redis_port, db=0)


class CacheService:
    """Cache service for managing Redis cache operations."""

    _redis: Redis
    """Redis client instance."""

    def __init__(self, redis: Redis) -> None:
        """Initialize the cache service.

        Args:
            redis: Redis client instance.
        """
        self._redis = redis
        self._prefix: str = settings.redis_prefix

    def _make_key(self, key: str) -> str:
        """Construct a cache key.

        Args:
            key: Base key.

        Returns:
            Constructed cache key.
        """
        return f"{self._prefix}:{key}"

    async def get_data(self, key: str) -> str | None:
        """Get data from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached data or None if not found.
        """
        return await self._redis.get(self._make_key(key))

    async def set_data(self, key: str, value: str, ttl: int) -> None:
        """Set data in the cache with a time-to-live (TTL).

        Args:
            key: Cache key.
            value: Data to cache.
            ttl: Time-to-live in seconds.
        """
        await self._redis.setex(self._make_key(key), ttl, value)


async def get_redis(request: Request) -> Redis:
    """Get Redis client. Initializes if not already present.

    Args:
        request: FastAPI request object.
    """
    if getattr(request.app.state, "redis", None) is not None:
        return request.app.state.redis

    async with _redis_lock:
        if getattr(request.app.state, "redis", None) is not None:
            return request.app.state.redis

        try:
            redis_client: Redis = Redis(connection_pool=pool)
            request.app.state.redis = redis_client
        except Exception as e:
            request.app.state.redis = None
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Redis service unavailable",
            ) from e
        return redis_client
