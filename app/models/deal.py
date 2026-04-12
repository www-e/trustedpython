"""
Deal and Payment models for transactions.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.listing import Listing
    from app.models.user import User
    from app.models.mediator import Mediator
    from app.models.review import Review


class Deal(Base, TimestampMixin):
    """
    Transactions between buyers, sellers, and mediators.

    Represents purchase deals for accounts/listings with payment tracking.
    """

    __tablename__ = "deals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    listing_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("listings.id"), nullable=True)
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    seller_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mediator_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending", nullable=False)
    total_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EGP", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chat_room_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="deals")
    listing: Mapped[Optional["Listing"]] = relationship("Listing", back_populates="deals")
    buyer: Mapped["User"] = relationship(
        "User", back_populates="purchases", foreign_keys=[buyer_id]
    )
    seller: Mapped["User"] = relationship("User", back_populates="sales", foreign_keys=[seller_id])
    mediator: Mapped[Optional["User"]] = relationship(
        "User", back_populates="mediated_deals", foreign_keys=[mediator_id]
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="deal", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="deal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_deals_buyer_id", "buyer_id"),
        Index("idx_deals_seller_id", "seller_id"),
        Index("idx_deals_mediator_id", "mediator_id"),
        Index("idx_deals_status", "status"),
        Index("idx_deals_created_at", "created_at"),
        Index("idx_deals_user_status", "buyer_id", "status"),
        Index("idx_deals_seller_status", "seller_id", "status"),
    )


class Payment(Base, TimestampMixin):
    """
    Payment records for deals.

    Tracks payment screenshots and verification status.
    """

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    deal_id: Mapped[UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="pending", nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="payment")
    verifier: Mapped[Optional["User"]] = relationship(
        "User", back_populates="verified_payments", foreign_keys=[verified_by]
    )

    __table_args__ = (
        Index("idx_payments_deal_id", "deal_id"),
        Index("idx_payments_status", "status"),
    )
