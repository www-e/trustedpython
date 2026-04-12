"""
User-related models: User, UserProfile, Session.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.listing import Listing
    from app.models.deal import Deal, Payment
    from app.models.mediator import Mediator
    from app.models.chat import ChatParticipant, Message
    from app.models.notification import Notification, NotificationPreference
    from app.models.review import Review


class User(Base, TimestampMixin):
    """
    Core user authentication and identity.

    Represents user accounts with authentication credentials and status.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requires_password_change: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    two_factor_backup_codes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    login_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    security_questions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frozen_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    freeze_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="seller", cascade="all, delete-orphan"
    )
    listings: Mapped[List["Listing"]] = relationship(
        "Listing", back_populates="seller", cascade="all, delete-orphan"
    )
    purchases: Mapped[List["Deal"]] = relationship(
        "Deal", foreign_keys="Deal.buyer_id", back_populates="buyer", cascade="all, delete-orphan"
    )
    sales: Mapped[List["Deal"]] = relationship(
        "Deal", foreign_keys="Deal.seller_id", back_populates="seller", cascade="all, delete-orphan"
    )
    mediated_deals: Mapped[List["Deal"]] = relationship(
        "Deal",
        foreign_keys="Deal.mediator_id",
        back_populates="mediator",
        cascade="all, delete-orphan",
    )
    mediator_profile: Mapped["Mediator"] = relationship(
        "Mediator", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    chat_participations: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant", back_populates="user", cascade="all, delete-orphan"
    )
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped["NotificationPreference"] = relationship(
        "NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    given_reviews: Mapped[List["Review"]] = relationship(
        "Review",
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer",
        cascade="all, delete-orphan",
    )
    received_reviews: Mapped[List["Review"]] = relationship(
        "Review",
        foreign_keys="Review.reviewee_id",
        back_populates="reviewee",
        cascade="all, delete-orphan",
    )
    verified_payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        foreign_keys="Payment.verified_by",
        back_populates="verifier",
        cascade="all, delete-orphan",
    )


class UserProfile(Base, TimestampMixin):
    """
    Extended user profile information.

    Contains additional user details beyond authentication.
    """

    __tablename__ = "user_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_role: Mapped[str] = mapped_column(String(50), default="Trader", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    member_since: Mapped[Optional[date]] = mapped_column(nullable=True)
    completed_deals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.00, nullable=False)
    accounts_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bought_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0.00, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    __table_args__ = (Index("idx_user_profiles_user_id", "user_id"),)


class Session(Base):
    """
    Authentication sessions and tokens.

    Tracks user sessions with JWT tokens and device information.
    """

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    access_token_hash: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_access_token", "access_token_hash"),
        Index("idx_sessions_expires_at", "expires_at"),
    )


class SecurityEvent(Base):
    """
    Security events and audit log.

    Tracks security-related events for user accounts.
    """

    __tablename__ = "security_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, nullable=True  # Column name in database
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_security_events_user_id", "user_id"),
        Index("idx_security_events_event_type", "event_type"),
        Index("idx_security_events_timestamp", "timestamp"),
    )


class LoginHistory(Base):
    """
    Login history tracking.

    Tracks all login attempts including successful, failed, and suspicious logins.
    """

    __tablename__ = "login_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed, suspicious
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_login_history_user_id", "user_id"),
        Index("idx_login_history_timestamp", "timestamp"),
        Index("idx_login_history_status", "status"),
    )


class TrustedDevice(Base):
    """
    Trusted devices for 2FA bypass.

    Stores devices that have been marked as trusted to bypass 2FA.
    """

    __tablename__ = "trusted_devices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_info: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("idx_trusted_devices_user_id", "user_id"),)
