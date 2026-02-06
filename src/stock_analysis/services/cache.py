"""Cache service."""

from collections.abc import Awaitable
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from redis.asyncio import Redis

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from redis.asyncio import ConnectionPool
    from redis.asyncio.client import PubSub
    from redis.asyncio.lock import Lock

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

    async def set_data(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """Set data in the cache with a time-to-live (TTL).

        Args:
            key: Cache key.
            value: Data to cache.
            ttl: Time-to-live in seconds.

        Returns:
            True if the operation was successful.
        """
        return await self._redis.set(self._make_key(key), value, ex=ttl)

    async def set_data_if_not_exists(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """Set data in the cache only if the key does not already exist.

        Args:
            key: Cache key.
            value: Data to cache.
            ttl: Time-to-live in seconds.

        Returns:
            True if the key was set, False if it already exists.
        """
        return await self._redis.set(self._make_key(key), value, ex=ttl, nx=True)

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiration time for a cache key.

        Args:
            key: Cache key.
            ttl: Time-to-live in seconds.
        """
        await self._redis.expire(self._make_key(key), ttl)

    def acquire_lock(self, name: str, timeout: float | None = None) -> Lock:
        """Acquire a distributed lock.

        Args:
            name: Name for the lock.
            timeout: Lock timeout in seconds.

        Returns:
            Redis lock instance.
        """
        lock_name: str = self._make_key(f"lock:{name}:{uuid4().hex}")
        return self._redis.lock(lock_name, timeout=timeout, blocking=False)

    async def push_to_list(self, name: str, value: str) -> int:
        """Push a value to a Redis list.

        Args:
            name: List name.
            value: Value to push.

        Returns:
            Length of the list after the push.
        """
        result: Awaitable[int] | int = self._redis.rpush(self._make_key(name), value)
        return await result if isinstance(result, Awaitable) else result

    async def get_from_list(self, name: str, start: int, end: int) -> list[str]:
        """Get a range of values from a Redis list.

        Args:
            name: List name.
            start: Start index.
            end: End index.

        Returns:
            List of values from the specified range in the Redis list.
        """
        result: Awaitable[list[str]] | list[str] = self._redis.lrange(
            self._make_key(name), start, end
        )
        return await result if isinstance(result, Awaitable) else result

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a Redis channel.

        Args:
            channel: Channel name.
            message: Message to publish.

        Returns:
            Number of clients that received the message.
        """
        result: Awaitable[int] | int = self._redis.publish(
            self._make_key(channel), message
        )
        return await result if isinstance(result, Awaitable) else result

    async def subscribe(self, channel: str) -> PubSub:
        """Subscribe to a Redis channel.

        Args:
            channel: Channel name.

        Returns:
            Async generator yielding messages from the channel.
        """
        pubsub: PubSub = self._redis.pubsub()
        await pubsub.subscribe(self._make_key(channel))
        return pubsub

    async def unsubscribe(self, pubsub: PubSub, channel: str) -> None:
        """Unsubscribe from a Redis channel.

        Args:
            pubsub: PubSub instance.
            channel: Channel name.
        """
        await pubsub.unsubscribe(self._make_key(channel))


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
