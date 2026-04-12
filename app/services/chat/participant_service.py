"""
Participant service for chat operations.

Handles participant operations like marking messages as read and leaving chats.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chat import Message
from app.schemas.chat import MarkReadResponse
from app.services.chat.base import verify_participant_access
from app.utils.redis_pubsub import publish_to_channel


class ParticipantService:
    """
    Service for participant operations.

    Handles marking messages as read and leaving chat rooms.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize participant service.

        Args:
            db: Database session
        """
        self.db = db

    async def mark_chat_as_read(self, room_id: UUID, user_id: UUID) -> MarkReadResponse:
        """
        Mark all messages in a chat as read for a user.

        Args:
            room_id: Chat room ID
            user_id: User ID

        Returns:
            Number of messages marked as read

        Raises:
            AppException: If room not found or user not a participant
        """
        # Get participant
        participant = await verify_participant_access(self.db, room_id, user_id)

        # Get last_seen_at from user's last_login_at
        last_seen_at: Optional[datetime] = (
            participant.user.last_login_at if participant.user else None
        )

        # Count unread messages
        unread_query = (
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.room_id == room_id,
                    Message.sender_id != user_id,
                    Message.created_at > last_seen_at if last_seen_at else Message.created_at >= datetime.min
                )
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Publish to Redis
        await publish_to_channel(
            f"chat:{room_id}",
            {
                "event": "messages_read",
                "data": {
                    "room_id": str(room_id),
                    "user_id": str(user_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

        return MarkReadResponse(messages_marked_read=unread_count)

    async def leave_chat(self, room_id: UUID, user_id: UUID) -> None:
        """
        Leave a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID

        Raises:
            AppException: If room not found or user not a participant
        """
        # Get participant
        participant = await verify_participant_access(self.db, room_id, user_id)

        # Mark as left
        participant.left_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Publish to Redis
        await publish_to_channel(
            f"chat:{room_id}",
            {
                "event": "user_left",
                "data": {
                    "room_id": str(room_id),
                    "user_id": str(user_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
