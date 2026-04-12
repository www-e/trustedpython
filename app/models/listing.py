"""
Listing model for user-created listings.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.content import Category
    from app.models.deal import Deal


class Listing(Base, TimestampMixin):
    """
    User-created listings (alternative to accounts).

    Represents marketplace listings created by users for selling accounts.
    """

    __tablename__ = "listings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    seller_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    game: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="draft", nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default="Regular", nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    seller: Mapped["User"] = relationship(
        "User", back_populates="listings", foreign_keys=[seller_id]
    )
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="listings")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="listing")

    __table_args__ = (
        Index("idx_listings_seller_id", "seller_id"),
        Index("idx_listings_status", "status"),
        Index("idx_listings_game", "game"),
        Index("idx_listings_created_at", "created_at"),
    )
