"""
Base utilities and shared functionality for home services.

This module provides common helper functions used across home service modules.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def build_pagination_metadata(total: int, page: int, limit: int) -> Dict[str, Any]:
    """
    Build pagination metadata dictionary.

    Args:
        total: Total number of items
        page: Current page number
        limit: Items per page

    Returns:
        Dict with pagination metadata
    """
    return {"total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit}


async def get_entity_by_id_or_404(
    db: AsyncSession, model_class: type[Any], entity_id: UUID, error_message: str = "Entity not found"
) -> Any:
    """
    Get entity by ID or raise 404 error.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        entity_id: Entity UUID
        error_message: Custom error message

    Returns:
        Entity instance

    Raises:
        NotFoundException: If entity not found
    """
    from app.core.exceptions import NotFoundException

    result = await db.execute(select(model_class).where(model_class.id == entity_id))
    entity = result.scalar_one_or_none()

    if not entity:
        raise NotFoundException(error_message)

    return entity


def build_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Build a consistent cache key from prefix and arguments.

    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include
        **kwargs: Keyword arguments to include

    Returns:
        str: Formatted cache key
    """
    parts = [prefix]

    # Add positional args
    if args:
        parts.extend(str(arg) for arg in args)

    # Add keyword args (sorted for consistency)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

    return ":".join(parts)


from typing import Callable

async def get_cached_or_fetch(
    cache_service: Any, cache_key: str, fetch_func: Callable[[], Any], ttl: int = 300
) -> Any:
    """
    Get data from cache or fetch using provided function.

    Args:
        cache_service: Cache service instance
        cache_key: Cache key to use
        fetch_func: Async function to fetch data if not cached
        ttl: Cache TTL in seconds

    Returns:
        Cached or freshly fetched data
    """
    # Try to get from cache
    cached = await cache_service.get(cache_key)
    if cached is not None:
        return cached

    # Fetch fresh data
    data = await fetch_func()

    # Store in cache
    await cache_service.set(cache_key, data, ttl=ttl)

    return data
