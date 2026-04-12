"""
Chat room management service.

Handles chat room retrieval, details, and listing operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.chat import ChatParticipant, ChatRoom, Message
from app.schemas.chat import (
    ChatRoomDetailResponse,
    ChatRoomResponse,
    ChatRoomsListResponse,
    LastMessageResponse,
    ParticipantResponse,
)
from app.schemas.common import APIResponse, PaginationSchema
from app.services.chat.base import is_user_online, verify_participant_access


class RoomService:
    """
    Service for chat room management operations.

    Handles retrieving chat rooms, room details, and room listings.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize room service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_chat_rooms(
        self, user_id: UUID, room_type: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> APIResponse[ChatRoomsListResponse]:
        """
        Get all chat rooms for a user.

        Args:
            user_id: User ID
            room_type: Filter by room type (group/private)
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of chat rooms
        """
        # Build query for user's chat rooms
        query = (
            select(ChatRoom)
            .join(ChatParticipant, ChatParticipant.room_id == ChatRoom.id)
            .where(and_(ChatParticipant.user_id == user_id, ChatParticipant.left_at.is_(None)))
        )

        # Filter by type if specified
        if room_type:
            query = query.where(ChatRoom.type == room_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total: int = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(desc(ChatRoom.updated_at))
        query = query.offset((page - 1) * limit).limit(limit)

        # Execute query
        result = await self.db.execute(
            query.options(selectinload(ChatRoom.participants), selectinload(ChatRoom.messages))
        )
        rooms = result.scalars().all()

        # Build response
        rooms_data = []
        for room in rooms:
            # Get last message
            last_message = None
            if room.messages:
                msg = room.messages[0]
                last_message = LastMessageResponse(
                    id=str(msg.id),
                    sender_id=str(msg.sender_id),
                    sender_name=(
                        room.messages[0].sender.username if room.messages[0].sender else "Unknown"
                    ),
                    content=msg.content[:100] if msg.content else "",
                    type=msg.type,
                    timestamp=msg.created_at,
                )

            # Get participants (basic info)
            participants = []
            for participant in room.participants:
                if participant.left_at is None:
                    user_profile = participant.user.profile if participant.user else None
                    display_name = (
                        user_profile.display_name
                        if user_profile and user_profile.display_name
                        else participant.user.username
                    )
                    participants.append(
                        ParticipantResponse(
                            id=str(participant.user.id),
                            username=participant.user.username,
                            display_name=display_name,
                            avatar_url=(
                                user_profile.avatar_url
                                if user_profile
                                else None
                            ),
                            role=participant.role,
                            is_online=is_user_online(participant.user.last_login_at),
                            last_seen_at=participant.user.last_login_at,
                        )
                    )

            # Calculate unread count for the current user
            # Find the current user's participant record
            current_user_participant = None
            for part in room.participants:
                if part.user_id == user_id and part.left_at is None:
                    current_user_participant = part
                    break
            user_last_seen = (
                current_user_participant.user.last_login_at
                if current_user_participant and current_user_participant.user
                else None
            )
            unread_query = (
                select(func.count())
                .select_from(Message)
                .where(
                    and_(
                        Message.room_id == room.id,
                        Message.sender_id != user_id,
                        Message.created_at > user_last_seen if user_last_seen else Message.created_at >= datetime.min,
                    )
                )
            )
            unread_result = await self.db.execute(unread_query)
            unread_count = unread_result.scalar() or 0

            rooms_data.append(
                ChatRoomResponse(
                    id=str(room.id),
                    name=room.name or "Chat",
                    avatar=room.avatar,
                    type=room.type,
                    participants=participants,
                    last_message=last_message,
                    unread_count=unread_count,
                    last_message_time=(
                        room.messages[0].created_at if room.messages else room.created_at
                    ),
                    is_active=room.is_active,
                    created_at=room.created_at,
                )
            )

        # Create pagination
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return APIResponse.success_response(
            data=ChatRoomsListResponse(rooms=rooms_data), pagination=pagination
        )

    async def get_chat_room_details(self, room_id: UUID, user_id: UUID) -> ChatRoomDetailResponse:
        """
        Get detailed information about a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID (for access verification)

        Returns:
            Chat room details

        Raises:
            AppException: If room not found or user not a participant
        """
        # Verify user is a participant
        participant = await verify_participant_access(self.db, room_id, user_id)

        # Get room details
        room_query = (
            select(ChatRoom)
            .where(ChatRoom.id == room_id)
            .options(selectinload(ChatRoom.participants))
        )
        room_result = await self.db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise AppException("CHAT_ERROR", "Chat room not found", status_code=404)

        # Build participants list with full info
        participants = []
        for p in room.participants:
            if p.left_at is None:
                p_user_profile = p.user.profile if p.user else None
                p_display_name = (
                    p_user_profile.display_name
                    if p_user_profile and p_user_profile.display_name
                    else p.user.username
                )
                participants.append(
                    ParticipantResponse(
                        id=str(p.user.id),
                        username=p.user.username,
                        display_name=p_display_name,
                        avatar_url=p_user_profile.avatar_url if p_user_profile else None,
                        role=p.role,
                        is_online=is_user_online(p.user.last_login_at),
                        last_seen_at=p.user.last_login_at,
                    )
                )

        # Build metadata
        metadata = {}
        if room.deal_id:
            metadata["deal_id"] = str(room.deal_id)

        return ChatRoomDetailResponse(
            id=str(room.id),
            name=room.name or "Chat",
            avatar=room.avatar,
            type=room.type,
            participants=participants,
            created_at=room.created_at,
            metadata=metadata if metadata else None,
        )
