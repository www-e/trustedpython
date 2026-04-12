"""
Chat services package.

Provides specialized chat services for messaging operations.
This package maintains backward compatibility through the ChatService facade.

Usage:
    # Direct import (recommended for new code):
    from app.services.chat import RoomService, MessageService, ParticipantService

    # Facade import (for backward compatibility):
    from app.services.chat import ChatService
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.attachment_service import AttachmentService
from app.services.chat.message_service import MessageService
from app.services.chat.participant_service import ParticipantService
from app.services.chat.room_service import RoomService
from app.services.chat.unread_service import UnreadService

__all__ = [
    "RoomService",
    "MessageService",
    "ParticipantService",
    "AttachmentService",
    "UnreadService",
    "ChatService",  # Facade for backward compatibility
]


# Backward compatibility facade
class ChatService:
    """
    Facade for backward compatibility with legacy ChatService.

    This class provides the same interface as the original monolithic
    ChatService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize facade with database session.

        Args:
            db: Database session
        """
        self.db = db
        self._rooms: RoomService | None = None
        self._messages: MessageService | None = None
        self._participants: ParticipantService | None = None
        self._attachments: AttachmentService | None = None
        self._unread: UnreadService | None = None

    @property
    def rooms(self) -> RoomService:
        """Get room service instance."""
        if self._rooms is None:
            self._rooms = RoomService(self.db)
        return self._rooms

    @property
    def messages(self) -> MessageService:
        """Get message service instance."""
        if self._messages is None:
            self._messages = MessageService(self.db)
        return self._messages

    @property
    def participants(self) -> ParticipantService:
        """Get participant service instance."""
        if self._participants is None:
            self._participants = ParticipantService(self.db)
        return self._participants

    @property
    def attachments(self) -> AttachmentService:
        """Get attachment service instance."""
        if self._attachments is None:
            self._attachments = AttachmentService(self.db)
        return self._attachments

    @property
    def unread(self) -> UnreadService:
        """Get unread service instance."""
        if self._unread is None:
            self._unread = UnreadService(self.db)
        return self._unread

    # Room management methods - delegate to room service
    async def get_user_chat_rooms(
        self,
        user_id: Any,
        room_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
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
        return await self.rooms.get_user_chat_rooms(
            user_id=user_id, room_type=room_type, page=page, limit=limit
        )

    async def get_chat_room_details(self, room_id: Any, user_id: Any) -> Any:
        """
        Get detailed information about a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID (for access verification)

        Returns:
            Chat room details
        """
        return await self.rooms.get_chat_room_details(room_id=room_id, user_id=user_id)

    # Message methods - delegate to message service
    async def get_room_messages(
        self, room_id: Any, user_id: Any, before: Any = None, limit: int = 50
    ) -> Any:
        """
        Get messages for a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID (for access verification)
            before: Get messages before this timestamp
            limit: Number of messages to return

        Returns:
            List of messages
        """
        return await self.messages.get_room_messages(
            room_id=room_id, user_id=user_id, before=before, limit=limit
        )

    async def send_message(self, room_id: Any, user_id: Any, data: Any) -> Any:
        """
        Send a message to a chat room.

        Args:
            room_id: Chat room ID
            user_id: Sender user ID
            data: Message data

        Returns:
            Created message
        """
        return await self.messages.send_message(room_id=room_id, user_id=user_id, data=data)

    async def delete_message(self, message_id: Any, user_id: Any) -> None:
        """
        Delete a message (only sender can delete their messages).

        Args:
            message_id: Message ID
            user_id: User ID
        """
        await self.messages.delete_message(message_id=message_id, user_id=user_id)

    # Participant methods - delegate to participant service
    async def mark_chat_as_read(self, room_id: Any, user_id: Any) -> Any:
        """
        Mark all messages in a chat as read for a user.

        Args:
            room_id: Chat room ID
            user_id: User ID

        Returns:
            Number of messages marked as read
        """
        return await self.participants.mark_chat_as_read(room_id=room_id, user_id=user_id)

    async def leave_chat(self, room_id: Any, user_id: Any) -> None:
        """
        Leave a chat room.

        Args:
            room_id: Chat room ID
            user_id: User ID
        """
        await self.participants.leave_chat(room_id=room_id, user_id=user_id)

    # Attachment methods - delegate to attachment service
    async def upload_attachment(self, file: Any, room_id: Any, user_id: Any) -> Any:
        """
        Upload a file attachment for a message.

        Args:
            file: File to upload
            room_id: Chat room ID
            user_id: User ID

        Returns:
            Uploaded attachment info
        """
        return await self.attachments.upload_attachment(file=file, room_id=room_id, user_id=user_id)

    # Unread count methods - delegate to unread service
    async def get_unread_count(self, user_id: Any) -> Any:
        """
        Get total unread message count for a user.

        Args:
            user_id: User ID

        Returns:
            Total unread count
        """
        return await self.unread.get_unread_count(user_id=user_id)
