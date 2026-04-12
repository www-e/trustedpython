"""
Chat service for business logic.
"""

import html
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.chat import ChatParticipant, ChatRoom, Message, MessageAttachment
from app.models.user import User
from app.schemas.chat import (
    ChatRoomDetailResponse,
    ChatRoomResponse,
    ChatRoomsListResponse,
    LastMessageResponse,
    MarkReadResponse,
    MessageAttachmentResponse,
    MessageResponse,
    MessagesListResponse,
    ParticipantResponse,
    SendMessageRequest,
    UnreadCountResponse,
)
from app.schemas.common import APIResponse, PaginationSchema
from app.utils.redis_pubsub import publish_to_channel
from app.utils.storage import upload_file_to_storage


class ChatService:
    """
    Service for chat operations.

    Handles chat room management, messaging, and participant operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize chat service.

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
        total = total_result.scalar() or 0

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
                    participants.append(
                        ParticipantResponse(
                            id=str(participant.user.id),
                            username=participant.user.username,
                            display_name=(
                                participant.user.profile.display_name
                                if participant.user.profile and participant.user.profile.display_name
                                else participant.user.username
                            ),
                            avatar_url=(
                                participant.user.profile.avatar_url
                                if participant.user.profile
                                else None
                            ),
                            role=participant.role,
                            is_online=bool(
                                participant.user.last_login_at
                                and (
                                    datetime.now(timezone.utc) - participant.user.last_login_at
                                ).total_seconds()
                                < 300
                            ),
                            last_seen_at=participant.user.last_login_at,
                        )
                    )

            # Calculate unread count
            unread_conditions = [
                Message.room_id == room.id,
                Message.sender_id != user_id,
            ]
            if participant and participant.last_seen_at:
                unread_conditions.append(Message.created_at > participant.last_seen_at)

            unread_query = (
                select(func.count())
                .select_from(Message)
                .join(
                    ChatParticipant,
                    and_(
                        ChatParticipant.room_id == Message.room_id,
                        ChatParticipant.user_id == user_id,
                    ),
                )
                .where(and_(*unread_conditions))
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
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

        # Get room details
        room_query = (
            select(ChatRoom)
            .where(ChatRoom.id == room_id)
            .options(selectinload(ChatRoom.participants))
        )
        room_result = await self.db.execute(room_query)
        room = room_result.scalar_one_or_none()

        if not room:
            raise AppException("CHAT_ERROR", "Chat room not found", 404)

        # Build participants list with full info
        participants = []
        for p in room.participants:
            if p.left_at is None:
                is_online = bool(
                    p.user.last_login_at
                    and (datetime.now(timezone.utc) - p.user.last_login_at).total_seconds() < 300
                )

                participants.append(
                    ParticipantResponse(
                        id=str(p.user.id),
                        username=p.user.username,
                        display_name=(
                            p.user.profile.display_name
                            if p.user.profile and p.user.profile.display_name
                            else p.user.username
                        ),
                        avatar_url=p.user.profile.avatar_url if p.user.profile else None,
                        role=p.role,
                        is_online=is_online,
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

    async def get_room_messages(
        self, room_id: UUID, user_id: UUID, before: Optional[datetime] = None, limit: int = 50
    ) -> MessagesListResponse:
        """
        Get messages for a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID (for access verification)
            before: Get messages before this timestamp
            limit: Number of messages to return

        Returns:
            List of messages

        Raises:
            AppException: If room not found or user not a participant
        """
        # Verify user is a participant
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

        # Build messages query
        query = (
            select(Message).where(Message.room_id == room_id).where(Message.is_deleted.is_(False))
        )

        # Apply time filter
        if before:
            query = query.where(Message.created_at < before)

        # Order and limit
        query = query.order_by(desc(Message.created_at)).limit(limit)

        # Execute query
        result = await self.db.execute(query.options(selectinload(Message.attachments)))
        messages = result.scalars().all()

        # Build response
        messages_data = []
        for message in reversed(messages):  # Return in chronological order
            attachments = [
                MessageAttachmentResponse(
                    id=str(att.id),
                    url=att.url,
                    filename=att.filename,
                    size=att.size_bytes or 0,
                    mime_type=att.mime_type,
                )
                for att in message.attachments
            ]

            messages_data.append(
                MessageResponse(
                    id=str(message.id),
                    sender_id=str(message.sender_id),
                    sender_name=message.sender.username if message.sender else "Unknown",
                    sender_avatar=(
                        message.sender.profile.avatar_url
                        if message.sender and message.sender.profile
                        else None
                    ),
                    content=message.content,
                    type=message.type,
                    timestamp=message.created_at,
                    is_read=(
                        message.created_at <= participant.last_seen_at
                        if participant.last_seen_at
                        else False
                    ),
                    attachments=attachments,
                )
            )

        # Check if there are more messages
        has_more = len(messages) == limit

        return MessagesListResponse(messages=messages_data, has_more=has_more)

    async def send_message(
        self, room_id: UUID, user_id: UUID, data: SendMessageRequest
    ) -> MessageResponse:
        """
        Send a message to a chat room.

        Args:
            room_id: Chat room ID
            user_id: Sender user ID
            data: Message data

        Returns:
            Created message

        Raises:
            AppException: If room not found or user not a participant
        """
        # Sanitize message content to prevent XSS
        content = html.escape(data.content)

        # Verify user is a participant
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

        # Create message
        message = Message(
            id=uuid4(),
            room_id=room_id,
            sender_id=user_id,
            content=content,
            type=data.type,
            reply_to_message_id=data.reply_to_message_id,
        )

        self.db.add(message)

        # Update room timestamp
        await self.db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
        room = await self.db.get(ChatRoom, room_id)
        if room:
            room.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(message)

        # Publish to Redis for WebSocket clients
        await publish_to_channel(
            f"chat:{room_id}",
            {
                "event": "message",
                "data": {
                    "id": str(message.id),
                    "room_id": str(room_id),
                    "sender_id": str(user_id),
                    "content": content,
                    "type": data.type,
                    "timestamp": message.created_at.isoformat(),
                },
            },
        )

        return MessageResponse(
            id=str(message.id),
            sender_id=str(user_id),
            sender_name=participant.user.username if participant.user else "Unknown",
            sender_avatar=(
                participant.user.profile.avatar_url
                if participant.user and participant.user.profile
                else None
            ),
            content=content,
            type=data.type,
            timestamp=message.created_at,
            is_read=False,
            attachments=[],
        )

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
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

        # Count unread messages
        if participant.last_seen_at is not None:
            unread_condition = Message.created_at > participant.last_seen_at
        else:
            unread_condition = True  # type: ignore[assignment]

        unread_query = (
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.room_id == room_id,
                    Message.sender_id != user_id,
                    unread_condition,
                )
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Update last seen
        participant.last_seen_at = datetime.now(timezone.utc)
        await self.db.commit()

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
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

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

    async def upload_attachment(
        self, file: UploadFile, room_id: UUID, user_id: UUID
    ) -> MessageAttachmentResponse:
        """
        Upload a file attachment for a message.

        Args:
            file: File to upload
            room_id: Chat room ID
            user_id: User ID

        Returns:
            Uploaded attachment info

        Raises:
            AppException: If upload fails or user not a participant
        """
        # Verify user is a participant
        participant_query = select(ChatParticipant).where(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None),
            )
        )
        participant_result = await self.db.execute(participant_query)
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise AppException("CHAT_ERROR", "You are not a participant in this chat room", 403)

        # Upload file to storage
        try:
            file_url = await upload_file_to_storage(file=file, folder="chat-attachments")
        except Exception as e:
            raise AppException(
                error_code="CHAT_ERROR",
                message=f"Failed to upload file: {str(e)}",
                status_code=500
            )

        # Create attachment record (without message_id for now)
        attachment = MessageAttachment(
            id=uuid4(),
            message_id=uuid4(),  # Temporary, will be linked when message is sent
            url=file_url,
            filename=file.filename,
            size_bytes=0,  # Would need to read file.size
            mime_type=file.content_type,
        )

        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)

        return MessageAttachmentResponse(
            id=str(attachment.id),
            url=attachment.url,
            filename=attachment.filename,
            size=attachment.size_bytes or 0,
            mime_type=attachment.mime_type,
        )

    async def delete_message(self, message_id: UUID, user_id: UUID) -> None:
        """
        Delete a message (only sender can delete their messages).

        Args:
            message_id: Message ID
            user_id: User ID

        Raises:
            AppException: If message not found or user not the sender
        """
        # Get message
        message = await self.db.get(Message, message_id)

        if not message:
            raise AppException("CHAT_ERROR", "Message not found", 404)

        # Verify user is the sender
        if message.sender_id != user_id:
            raise AppException("CHAT_ERROR", "You can only delete your own messages", 403)

        # Soft delete
        message.is_deleted = True
        message.content = "[Message deleted]"
        await self.db.commit()

        # Publish to Redis
        await publish_to_channel(
            f"chat:{message.room_id}",
            {
                "event": "message_deleted",
                "data": {
                    "message_id": str(message_id),
                    "room_id": str(message.room_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

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
