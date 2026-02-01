"""Cache service."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from redis.asyncio import Redis

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from redis.asyncio import ConnectionPool

    from stock_analysis.settings import Settings


class CacheService:
    """Cache service for managing Redis cache operations."""

    _redis: Redis
    """Redis client instance."""

    def __init__(self, redis: Redis) -> None:
        """Initialize the cache service.

        Args:
            redis: Redis client instance.
        """
        settings: Settings = get_settings()
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
    """Get Redis client.

    Args:
        request: FastAPI request object.

    Returns:
        Redis client instance.

    Raises:
        HTTPException: If Redis service is unavailable.
    """
    pool: ConnectionPool | None = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )

    return Redis(connection_pool=pool)
