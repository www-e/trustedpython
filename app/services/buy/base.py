"""
Base utilities and shared functionality for buy services.

This module provides common helper functions used across buy service modules.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
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


def calculate_price_range(prices: list[float]) -> Dict[str, float]:
    """
    Calculate price range statistics.

    Args:
        prices: List of prices

    Returns:
        Dict with min, max, avg prices
    """
    if not prices:
        return {"min": 0, "max": 0, "avg": 0}

    return {"min": min(prices), "max": max(prices), "avg": round(sum(prices) / len(prices), 2)}


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
