"""
Message service for chat operations.

Handles message retrieval, sending, and deletion.
"""

import html
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.chat import ChatRoom, Message, MessageAttachment
from app.schemas.chat import MessageAttachmentResponse, MessageResponse, MessagesListResponse, SendMessageRequest
from app.services.chat.base import verify_participant_access
from app.utils.redis_pubsub import publish_to_channel


class MessageService:
    """
    Service for message operations.

    Handles retrieving, sending, and deleting messages in chat rooms.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize message service.

        Args:
            db: Database session
        """
        self.db = db

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
        participant = await verify_participant_access(self.db, room_id, user_id)

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
        # Get last_seen_at from user's last_login_at
        last_seen_at = participant.user.last_login_at if participant.user else None
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

            sender_username = "Unknown"
            sender_avatar_url = None
            if message.sender:
                sender_username = message.sender.username or "Unknown"
                if message.sender.profile:
                    sender_avatar_url = message.sender.profile.avatar_url

            messages_data.append(
                MessageResponse(
                    id=str(message.id),
                    sender_id=str(message.sender_id),
                    sender_name=sender_username,
                    sender_avatar=sender_avatar_url,
                    content=message.content,
                    type=message.type,
                    timestamp=message.created_at,
                    is_read=(
                        message.created_at <= last_seen_at
                        if last_seen_at
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
        participant = await verify_participant_access(self.db, room_id, user_id)

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
            sender_name=participant.user.username if participant.user and participant.user.username else "Unknown",
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
            raise AppException("CHAT_ERROR", "Message not found", status_code=404)

        # Verify user is the sender
        if message.sender_id != user_id:
            raise AppException("CHAT_ERROR", "You can only delete your own messages", status_code=403)

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
