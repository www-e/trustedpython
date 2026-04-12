"""
Redis client configuration and initialization.
"""

from typing import Optional

import redis.asyncio as redis

from app.core.config import settings

# Global Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """
    Initialize Redis connection.
    Should be called on application startup.
    """
    global redis_client

    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        if redis_client:
            await redis_client.ping()
        print("[OK] Redis connected successfully")

    except Exception as e:
        print(f"[WARNING] Redis connection failed: {e}")
        redis_client = None


async def close_redis() -> None:
    """
    Close Redis connection.
    Should be called on application shutdown.
    """
    global redis_client

    if redis_client:
        await redis_client.close()
        redis_client = None
        print("[OK] Redis connection closed")


async def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client instance.

    Returns:
        Redis client or None if not connected
    """
    return redis_client
