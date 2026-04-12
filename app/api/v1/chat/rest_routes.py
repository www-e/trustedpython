"""
Chat REST API routes.

Provides endpoints for chat room management, messaging, and file uploads.
WebSocket endpoints are handled separately in routes.py.
"""

from logging import getLogger
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.chat import (
    ChatRoomDetailResponse,
    ChatRoomResponse,
    ChatRoomsListResponse,
    MarkReadResponse,
    MessageAttachmentResponse,
    MessageResponse,
    MessagesListResponse,
    SendMessageRequest,
    UnreadCountResponse,
)
from app.schemas.common import APIResponse, SuccessResponse
from app.services.chat_service import ChatService
from app.utils.rate_limit import rate_limit_chat_message

logger = getLogger(__name__)
router = APIRouter()


@router.get(
    "/rooms",
    response_model=APIResponse[ChatRoomsListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user's chat rooms",
)
async def get_chat_rooms(
    room_type: Optional[str] = Query(None, description="Filter by room type: 'group' or 'private'"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ChatRoomsListResponse]:
    """
    Get all chat rooms for the authenticated user.

    Supports filtering by room type and pagination.
    Returns list of chat rooms with last message preview and unread counts.
    """
    try:
        chat_service = ChatService(db)
        result = await chat_service.get_user_chat_rooms(
            user_id=current_user.id, room_type=room_type, page=page, limit=limit
        )

        logger.info(f"User {current_user.username} fetched chat rooms")
        return result

    except AppException as e:
        logger.warning(f"Failed to fetch chat rooms: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error fetching chat rooms: {str(e)}")
        raise


@router.get(
    "/rooms/{room_id}",
    response_model=APIResponse[ChatRoomDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get chat room details",
)
async def get_chat_room_details(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ChatRoomDetailResponse]:
    """
    Get detailed information about a specific chat room.

    Returns full participant list with online status and room metadata.
    User must be a participant to access the room.
    """
    try:
        chat_service = ChatService(db)
        result = await chat_service.get_chat_room_details(room_id=room_id, user_id=current_user.id)

        logger.info(f"User {current_user.username} fetched room {room_id}")
        return APIResponse.success_response(data=result)

    except AppException as e:
        logger.warning(f"Failed to fetch room details: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error fetching room details: {str(e)}")
        raise


@router.get(
    "/rooms/{room_id}/messages",
    response_model=APIResponse[MessagesListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get messages for a chat room",
)
async def get_room_messages(
    room_id: UUID,
    before: Optional[str] = Query(
        None, description="Get messages before this timestamp (ISO 8601)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MessagesListResponse]:
    """
    Get messages for a specific chat room.

    Messages are returned in chronological order (oldest first).
    Supports pagination using the 'before' timestamp parameter.
    User must be a participant to access messages.
    """
    try:
        from datetime import datetime

        # Parse timestamp if provided
        before_dt = None
        if before:
            try:
                before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
            except ValueError:
                raise AppException(
                    "INVALID_TIMESTAMP", "Invalid timestamp format. Use ISO 8601 format.", 400
                )

        chat_service = ChatService(db)
        result = await chat_service.get_room_messages(
            room_id=room_id, user_id=current_user.id, before=before_dt, limit=limit
        )

        logger.info(f"User {current_user.username} fetched messages for room {room_id}")
        return APIResponse.success_response(data=result)

    except AppException as e:
        logger.warning(f"Failed to fetch messages: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise


@router.post(
    "/rooms/{room_id}/messages",
    response_model=APIResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
)
@rate_limit_chat_message
async def send_message(
    room_id: UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MessageResponse]:
    """
    Send a message to a chat room.

    Message content is sanitized to prevent XSS attacks.
    Supports replies to existing messages.
    User must be a participant to send messages.
    Real-time delivery via WebSocket.
    """
    try:
        chat_service = ChatService(db)
        result = await chat_service.send_message(
            room_id=room_id, user_id=current_user.id, data=data
        )

        logger.info(f"User {current_user.username} sent message to room {room_id}")
        return APIResponse.success_response(data=result, message="Message sent successfully")

    except AppException as e:
        logger.warning(f"Failed to send message: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise


@router.post(
    "/rooms/{room_id}/read",
    response_model=APIResponse[MarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark chat as read",
)
async def mark_chat_as_read(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MarkReadResponse]:
    """
    Mark all messages in a chat as read.

    Updates the user's last seen timestamp for the room.
    User must be a participant to mark as read.
    """
    try:
        chat_service = ChatService(db)
        result = await chat_service.mark_chat_as_read(room_id=room_id, user_id=current_user.id)

        logger.info(f"User {current_user.username} marked room {room_id} as read")
        return APIResponse.success_response(data=result, message="Messages marked as read")

    except AppException as e:
        logger.warning(f"Failed to mark as read: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error marking as read: {str(e)}")
        raise


@router.delete(
    "/rooms/{room_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave a chat room",
)
async def leave_chat(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Leave a chat room.

    Removes the user from the room's participant list.
    User will no longer receive messages from this room.
    For private chats, this may delete the room.
    """
    try:
        chat_service = ChatService(db)
        await chat_service.leave_chat(room_id=room_id, user_id=current_user.id)

        logger.info(f"User {current_user.username} left room {room_id}")
        return SuccessResponse.create(message="Left chat room successfully")

    except AppException as e:
        logger.warning(f"Failed to leave room: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error leaving room: {str(e)}")
        raise


@router.post(
    "/upload",
    response_model=APIResponse[MessageAttachmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload message attachment",
)
async def upload_attachment(
    file: UploadFile = File(..., description="File to upload"),
    room_id: UUID = Form(..., description="Target chat room ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MessageAttachmentResponse]:
    """
    Upload a file attachment for a message.

    Supported file types: jpg, jpeg, png, gif, pdf, doc, docx
    Maximum file size: 10MB
    User must be a participant in the target room.

    Returns attachment info that can be included when sending a message.
    """
    try:
        # Validate file size (10MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise AppException("UPLOAD_ERROR", "File size exceeds 10MB limit", status_code=400)

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
        filename = file.filename or ""
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext not in allowed_extensions:
            raise AppException(
                "UPLOAD_ERROR",
                f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}",
                status_code=400,
            )

        # Reset file pointer
        await file.seek(0)

        chat_service = ChatService(db)
        result = await chat_service.upload_attachment(
            file=file, room_id=room_id, user_id=current_user.id
        )

        logger.info(f"User {current_user.username} uploaded attachment for room {room_id}")
        return APIResponse.success_response(data=result, message="File uploaded successfully")

    except AppException as e:
        logger.warning(f"Failed to upload attachment: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error uploading attachment: {str(e)}")
        raise


@router.delete(
    "/messages/{message_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a message",
)
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Delete a message.

    Only the message sender can delete their own messages.
    Message is soft-deleted (content replaced with placeholder).
    """
    try:
        chat_service = ChatService(db)
        await chat_service.delete_message(message_id=message_id, user_id=current_user.id)

        logger.info(f"User {current_user.username} deleted message {message_id}")
        return SuccessResponse.create(message="Message deleted successfully")

    except AppException as e:
        logger.warning(f"Failed to delete message: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")
        raise


@router.get(
    "/unread-count",
    response_model=APIResponse[UnreadCountResponse],
    status_code=status.HTTP_200_OK,
    summary="Get unread message count",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[UnreadCountResponse]:
    """
    Get total unread message count across all chat rooms.

    Returns the total number of unread messages for the authenticated user.
    """
    try:
        chat_service = ChatService(db)
        result = await chat_service.get_unread_count(current_user.id)

        logger.info(f"User {current_user.username} fetched unread count")
        return APIResponse.success_response(data=result)

    except AppException as e:
        logger.warning(f"Failed to fetch unread count: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error fetching unread count: {str(e)}")
        raise
