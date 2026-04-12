"""
Account-related models: Account, AccountImage, AccountFeature.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.deal import Deal


class Account(Base, TimestampMixin):
    """
    Game accounts available for sale.

    Represents individual game accounts that users can purchase.
    """

    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    seller_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    game: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    rank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EGP", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, default="active", nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    seller: Mapped["User"] = relationship(
        "User", back_populates="accounts", foreign_keys=[seller_id]
    )
    images: Mapped[List["AccountImage"]] = relationship(
        "AccountImage",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="AccountImage.display_order",
    )
    features: Mapped[List["AccountFeature"]] = relationship(
        "AccountFeature", back_populates="account", cascade="all, delete-orphan"
    )
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="account")

    __table_args__ = (
        Index("idx_accounts_seller_id", "seller_id"),
        Index("idx_accounts_game", "game"),
        Index("idx_accounts_status", "status"),
        Index("idx_accounts_price", "price"),
        Index("idx_accounts_created_at", "created_at"),
        Index("idx_accounts_game_price", "game", "price"),
    )


class AccountImage(Base):
    """
    Images for game accounts.

    Stores image URLs and metadata for account listings.
    """

    __tablename__ = "account_images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="images")

    __table_args__ = (Index("idx_account_images_account_id", "account_id"),)


class AccountFeature(Base):
    """
    Features/badges for accounts.

    Represents special features, achievements, or badges for game accounts.
    """

    __tablename__ = "account_features"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="features")

    __table_args__ = (Index("idx_account_features_account_id", "account_id"),)
