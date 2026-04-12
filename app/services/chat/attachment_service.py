"""
Attachment service for chat operations.

Handles file uploads for message attachments.
"""

from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chat import MessageAttachment
from app.schemas.chat import MessageAttachmentResponse
from app.services.chat.base import verify_participant_access
from app.utils.storage import upload_file_to_storage


class AttachmentService:
    """
    Service for attachment operations.

    Handles file uploads for chat message attachments.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize attachment service.

        Args:
            db: Database session
        """
        self.db = db

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
        await verify_participant_access(self.db, room_id, user_id)

        # Upload file to storage
        try:
            file_url = await upload_file_to_storage(file=file, folder="chat-attachments")
        except Exception as e:
            raise AppException("CHAT_ERROR", f"Failed to upload file: {str(e)}", status_code=500)

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
