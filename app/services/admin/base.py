"""
Base utilities and shared functionality for admin services.

This module provides common helper functions used across all admin service modules.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def verify_admin_access(user: User) -> None:
    """
    Verify that the current user has admin access.

    Args:
        user: Current authenticated user

    Raises:
        ForbiddenException: If user is not an admin
    """
    from app.core.exceptions import ForbiddenException

    # Check if user is verified (temporary admin check)
    if not user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here when User model has role field
    # if user.role != "admin":
    #     raise ForbiddenException("access admin panel")


async def get_entity_count(
    db: AsyncSession, model_class: type[Any], filters: Optional[list] = None
) -> int:
    """
    Get count of entities with optional filters.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        filters: Optional list of filter conditions

    Returns:
        int: Count of matching entities
    """
    query = select(func.count(model_class.id))
    if filters:
        query = query.where(*filters)
    return await db.scalar(query) or 0


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


def format_audit_action(
    admin_id: UUID,
    action: str,
    entity_type: str,
    entity_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Format an admin action for audit logging.

    Args:
        admin_id: ID of the admin performing the action
        action: Action performed (e.g., 'verify_user', 'ban_user')
        entity_type: Type of entity affected (e.g., 'user', 'listing')
        entity_id: ID of the affected entity
        details: Additional action details

    Returns:
        Dict formatted for audit log
    """
    return {
        "admin_id": str(admin_id),
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
