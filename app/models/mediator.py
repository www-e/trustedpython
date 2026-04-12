"""
Mediator-related models: Mediator, MediatorBadge.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Mediator(Base, TimestampMixin):
    """
    Mediator profiles.

    Represents users who act as mediators for transactions.
    """

    __tablename__ = "mediators"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rating: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.00, nullable=False)
    program_rating: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.00, nullable=False)
    transactions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    response_time: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), index=True, default="bronze", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avg_response_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    member_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    experience: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    response_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    avg_response_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="mediator_profile", foreign_keys=[user_id]
    )
    badges: Mapped[List["MediatorBadge"]] = relationship(
        "MediatorBadge", back_populates="mediator", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_mediators_user_id", "user_id"),
        Index("idx_mediators_tier", "tier"),
        Index("idx_mediators_rating", "rating"),
    )


class MediatorBadge(Base):
    """
    Mediator achievements.

    Represents badges and achievements earned by mediators.
    """

    __tablename__ = "mediator_badges"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    mediator_id: Mapped[UUID] = mapped_column(
        ForeignKey("mediators.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    mediator: Mapped["Mediator"] = relationship("Mediator", back_populates="badges")

    __table_args__ = (Index("idx_mediator_badges_mediator_id", "mediator_id"),)


class MediatorApplication(Base, TimestampMixin):
    """
    Mediator applications.

    Represents applications from users to become mediators.
    """

    __tablename__ = "mediator_applications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="pending", nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    payment_methods: Mapped[List["MediatorPaymentMethod"]] = relationship(
        "MediatorPaymentMethod", back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_mediator_applications_user_id", "user_id"),
        Index("idx_mediator_applications_status", "status"),
    )


class MediatorPaymentMethod(Base):
    """
    Mediator payment methods.

    Represents payment methods accepted by a mediator applicant.
    """

    __tablename__ = "mediator_payment_methods"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("mediator_applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    method_type: Mapped[str] = mapped_column(String(50), nullable=False)
    method_name: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["MediatorApplication"] = relationship(
        "MediatorApplication", back_populates="payment_methods"
    )

    __table_args__ = (Index("idx_mediator_payment_methods_application_id", "application_id"),)
