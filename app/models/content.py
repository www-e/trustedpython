"""
Content models: Game, Category, PromoBanner, FAQItem.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.listing import Listing


class Game(Base, TimestampMixin):
    """
    Supported games.

    Represents games supported on the marketplace.
    """

    __tablename__ = "games"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, index=True, default=False, nullable=False)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_listings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="game", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_games_slug", "slug"),
        Index("idx_games_is_popular", "is_popular"),
    )


class Category(Base):
    """
    Listing categories.

    Represents categories for organizing listings.
    """

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    game_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("games.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    listing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    game: Mapped[Optional["Game"]] = relationship("Game", back_populates="categories")
    listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="category")


class PromoBanner(Base):
    """
    Marketing banners.

    Represents promotional banners displayed on the platform.
    """

    __tablename__ = "promo_banners"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, index=True, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, index=True, default=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("idx_promo_banners_is_active", "is_active"),
        Index("idx_promo_banners_priority", "priority"),
    )


class FAQItem(Base):
    """
    FAQ content.

    Represents frequently asked questions and answers.
    """

    __tablename__ = "faq_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, index=True, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("idx_faq_items_category", "category"),
        Index("idx_faq_items_display_order", "display_order"),
    )
