"""
Unread count service for chat operations.

Handles tracking and retrieving unread message counts.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatParticipant, Message
from app.schemas.chat import UnreadCountResponse


class UnreadService:
    """
    Service for unread message tracking.

    Handles calculating and retrieving unread message counts for users.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize unread service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_unread_count(self, user_id: UUID) -> UnreadCountResponse:
        """
        Get total unread message count for a user.

        Args:
            user_id: User ID

        Returns:
            Total unread count
        """
        # Get all rooms user is participating in
        participant_subquery = (
            select(ChatParticipant.room_id, ChatParticipant.last_seen_at)
            .where(and_(ChatParticipant.user_id == user_id, ChatParticipant.left_at.is_(None)))
            .subquery()
        )

        # Count unread messages
        unread_query = (
            select(func.count())
            .select_from(Message)
            .join(participant_subquery, Message.room_id == participant_subquery.c.room_id)
            .where(
                and_(
                    Message.sender_id != user_id,
                    Message.created_at > participant_subquery.c.last_seen_at,
                )
            )
        )

        result = await self.db.execute(unread_query)
        unread_count = result.scalar() or 0

        return UnreadCountResponse(unread_count=unread_count)
