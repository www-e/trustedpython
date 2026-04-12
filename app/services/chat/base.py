"""
Base utilities and shared functionality for chat services.

This module provides common helper functions used across all chat service modules.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chat import ChatParticipant


async def verify_participant_access(
    db: AsyncSession, room_id: UUID, user_id: UUID
) -> ChatParticipant:
    """
    Verify that a user is an active participant in a chat room.

    Args:
        db: Database session
        room_id: Chat room ID
        user_id: User ID

    Returns:
        ChatParticipant: The participant record

    Raises:
        AppException: If user is not a participant in the room
    """
    participant_query = select(ChatParticipant).where(
        and_(
            ChatParticipant.room_id == room_id,
            ChatParticipant.user_id == user_id,
            ChatParticipant.left_at.is_(None),
        )
    )
    participant_result = await db.execute(participant_query)
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise AppException(
            error_code="NOT_PARTICIPANT",
            message="You are not a participant in this chat room",
            status_code=403
        )

    return participant


def is_user_online(last_login_at: Optional[datetime]) -> bool:
    """
    Determine if a user is online based on their last login time.

    Args:
        last_login_at: User's last login timestamp

    Returns:
        bool: True if user is considered online (last login < 5 minutes ago)
    """
    if not last_login_at:
        return False

    time_since_login = (datetime.now(timezone.utc) - last_login_at).total_seconds()
    return time_since_login < 300  # Online if last login < 5 min ago
