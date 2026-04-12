"""
Chat schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ParticipantResponse(BaseModel):
    """Chat participant information."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    role: str = Field(..., description="Role in chat: admin or member")
    is_online: bool = Field(False, description="Online status")
    last_seen_at: Optional[datetime] = Field(None, description="Last seen timestamp")


class LastMessageResponse(BaseModel):
    """Last message preview in chat room."""

    id: str = Field(..., description="Message ID")
    sender_id: str = Field(..., description="Sender user ID")
    sender_name: str = Field(..., description="Sender username")
    content: str = Field(..., description="Message content (truncated if needed)")
    type: str = Field(..., description="Message type: text, image, or system")
    timestamp: datetime = Field(..., description="Message timestamp")


class ChatRoomResponse(BaseModel):
    """Chat room summary for list view."""

    id: str = Field(..., description="Chat room ID")
    name: str = Field(..., description="Room name (group) or other user name (private)")
    avatar: Optional[str] = Field(None, description="Room avatar URL")
    type: str = Field(..., description="Room type: group or private")
    participants: List[ParticipantResponse] = Field(
        default_factory=list, description="List of participants (basic info)"
    )
    last_message: Optional[LastMessageResponse] = Field(None, description="Last message in room")
    unread_count: int = Field(0, description="Number of unread messages")
    last_message_time: Optional[datetime] = Field(None, description="Timestamp of last message")
    is_active: bool = Field(..., description="Whether room is active")
    created_at: datetime = Field(..., description="Room creation timestamp")


class ChatRoomDetailResponse(BaseModel):
    """Full chat room details."""

    id: str = Field(..., description="Chat room ID")
    name: str = Field(..., description="Room name")
    avatar: Optional[str] = Field(None, description="Room avatar URL")
    type: str = Field(..., description="Room type: group or private")
    participants: List[ParticipantResponse] = Field(
        ..., description="List of participants with full info"
    )
    created_at: datetime = Field(..., description="Room creation timestamp")
    metadata: Optional[dict] = Field(
        None, description="Additional metadata (deal_id, account_id, etc.)"
    )


class MessageAttachmentResponse(BaseModel):
    """Message attachment information."""

    id: str = Field(..., description="Attachment ID")
    url: str = Field(..., description="Attachment URL")
    filename: Optional[str] = Field(None, description="Original filename")
    size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")


class MessageResponse(BaseModel):
    """Chat message response."""

    id: str = Field(..., description="Message ID")
    sender_id: str = Field(..., description="Sender user ID")
    sender_name: str = Field(..., description="Sender username")
    sender_avatar: Optional[str] = Field(None, description="Sender avatar URL")
    content: str = Field(..., description="Message content")
    type: str = Field(..., description="Message type: text, image, or system")
    timestamp: datetime = Field(..., description="Message timestamp")
    is_read: bool = Field(False, description="Whether message is read by recipient")
    attachments: List[MessageAttachmentResponse] = Field(
        default_factory=list, description="Message attachments"
    )


class MessagesListResponse(BaseModel):
    """Paginated list of messages."""

    messages: List[MessageResponse] = Field(
        default_factory=list, description="List of messages (newest first)"
    )
    has_more: bool = Field(..., description="Whether there are more messages to load")


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    type: str = Field("text", description="Message type: text, image, or system")
    reply_to_message_id: Optional[str] = Field(None, description="ID of message being replied to")


class MarkReadResponse(BaseModel):
    """Response for marking chat as read."""

    messages_marked_read: int = Field(..., description="Number of messages marked as read")


class ChatRoomsListResponse(BaseModel):
    """Response for chat rooms list."""

    rooms: List[ChatRoomResponse] = Field(default_factory=list, description="List of chat rooms")


class UnreadCountResponse(BaseModel):
    """Response for unread count."""

    unread_count: int = Field(..., description="Total unread messages across all chats")
