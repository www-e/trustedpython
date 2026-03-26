"""Listing and Category models."""

from sqlalchemy import Boolean, String, Text, Numeric, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.base import BaseModel
from app.models.user import User
from app.models.enums import ListingStatus, GameType

# Import for type hints (avoiding circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing_mediator import ListingMediator


class Category(BaseModel):
    """Category model for game types."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    icon_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_popular: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this category is shown in popular games section"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(
        "Listing",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class Listing(BaseModel):
    """Gaming account listing model."""

    __tablename__ = "listings"

    # Foreign Keys
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Listing Details
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    game_type: Mapped[GameType] = mapped_column(
        PgEnum(GameType, name="game_type", create_type=False),
        nullable=False
    )

    # Account Details
    level: Mapped[int | None] = mapped_column(Integer)
    rank: Mapped[str | None] = mapped_column(String(100))
    server: Mapped[str | None] = mapped_column(String(100))
    skins_count: Mapped[int | None] = mapped_column(Integer)
    characters_count: Mapped[int | None] = mapped_column(Integer)

    # Pricing
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Status
    status: Mapped[ListingStatus] = mapped_column(
        PgEnum(ListingStatus, name="listing_status", create_type=False),
        default=ListingStatus.DRAFT,
        nullable=False
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    views_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Relationships
    seller: Mapped["User"] = relationship(
        "User",
        back_populates="listings"
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="listings"
    )
    images: Mapped[list["ListingImage"]] = relationship(
        "ListingImage",
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="ListingImage.sort_order",
        lazy="selectin"
    )
    allowed_mediators: Mapped[list["ListingMediator"]] = relationship(
        "ListingMediator",
        back_populates="listing",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, title={self.title}, price={self.price})>"


class ListingImage(BaseModel):
    """Listing image model."""

    __tablename__ = "listing_images"

    # Foreign Key
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Image Details
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    caption: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(
        "Listing",
        back_populates="images"
    )

    def __repr__(self) -> str:
        return f"<ListingImage(id={self.id}, listing_id={self.listing_id})>"
