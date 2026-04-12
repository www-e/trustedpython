"""
Notification-related models: Notification, NotificationPreference.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """
    User notifications.

    Represents notifications sent to users about various events.
    """

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, index=True, default=False, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_type", "type"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_user_read", "user_id", "is_read", "created_at"),
    )


class NotificationPreference(Base, TimestampMixin):
    """
    User notification preferences.

    Stores user settings for how they want to receive notifications.
    """

    __tablename__ = "notification_prefs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    types: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "account_update": {"enabled": True, "push": True, "email": True},
            "message": {"enabled": True, "push": True, "email": True},
            "security_alert": {"enabled": True, "push": True, "email": True},
            "purchase": {"enabled": True, "push": True, "email": True},
            "system": {"enabled": True, "push": True, "email": True},
        },
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")
