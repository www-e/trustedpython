"""
Base utilities and shared functionality for security services.

This module provides common helper functions used across all security service modules.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SecurityEvent, Session, User


async def log_security_event(
    db: AsyncSession,
    user_id: UUID,
    event_type: str,
    metadata: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log security event to database.

    Args:
        db: Database session
        user_id: ID of the user
        event_type: Type of security event
        metadata: Event metadata dictionary
        ip_address: Optional IP address
        user_agent: Optional user agent string
    """
    event = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )

    db.add(event)
    await db.commit()


async def get_active_sessions_count(db: AsyncSession, user_id: UUID) -> int:
    """
    Get count of active sessions for a user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        int: Number of active sessions
    """
    from datetime import datetime

    sessions_result = await db.execute(
        select(func.count()).select_from(
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.revoked_at.is_(None),
                    Session.expires_at > datetime.utcnow(),
                )
            )
            .subquery()
        )
    )
    return sessions_result.scalar() or 0


async def get_failed_login_count(db: AsyncSession, user_id: UUID, days: int = 7) -> int:
    """
    Get count of failed login attempts in the specified time period.

    Args:
        db: Database session
        user_id: ID of the user
        days: Number of days to look back

    Returns:
        int: Number of failed login attempts
    """
    failed_logins_result = await db.execute(
        select(func.count()).select_from(
            select(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.user_id == user_id,
                    SecurityEvent.event_type == "login_failed",
                    SecurityEvent.timestamp
                    > datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days),
                )
            )
            .subquery()
        )
    )
    return failed_logins_result.scalar() or 0


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        User object or None if not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def build_pagination_metadata(total: int, page: int, page_size: int) -> Dict[str, Any]:
    """
    Build pagination metadata dictionary.

    Args:
        total: Total number of items
        page: Current page number
        page_size: Items per page

    Returns:
        Dict with pagination metadata
    """
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
