"""
Chat-related models: ChatRoom, ChatParticipant, Message, MessageAttachment.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.deal import Deal
    from app.models.user import User


class ChatRoom(Base, TimestampMixin):
    """
    Chat conversations.

    Represents a chat room for deal communication or general messaging.
    """

    __tablename__ = "chat_rooms"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deal_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("deals.id"), index=True, nullable=True
    )

    # Relationships
    participants: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant", back_populates="room", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="Message.created_at.desc()",
    )
    deal: Mapped[Optional["Deal"]] = relationship(
        "Deal", foreign_keys=[deal_id], backref="chat_room"
    )

    __table_args__ = (
        Index("idx_chat_rooms_type", "type"),
        Index("idx_chat_rooms_deal_id", "deal_id"),
    )


class ChatParticipant(Base):
    """
    Room memberships.

    Represents users who are members of a chat room.
    """

    __tablename__ = "chat_participants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="chat_participations")

    __table_args__ = (
        Index("idx_chat_participants_room_id", "room_id"),
        Index("idx_chat_participants_user_id", "user_id"),
        UniqueConstraint("room_id", "user_id", name="uq_room_user"),
    )


class Message(Base):
    """
    Chat messages.

    Represents individual messages sent in a chat room.
    """

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    reply_to_message_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("messages.id"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")
    sender: Mapped["User"] = relationship(
        "User", back_populates="sent_messages", foreign_keys=[sender_id]
    )
    reply_to: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], backref="replies"
    )
    attachments: Mapped[List["MessageAttachment"]] = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_messages_room_id", "room_id"),
        Index("idx_messages_sender_id", "sender_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_room_time", "room_id", "created_at"),
    )


class MessageAttachment(Base):
    """
    File attachments for messages.

    Stores file metadata for message attachments.
    """

    __tablename__ = "message_attachments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="attachments")

    __table_args__ = (Index("idx_message_attachments_message_id", "message_id"),)
