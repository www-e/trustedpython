"""User model."""

from sqlalchemy import Boolean, String, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import UserRole

# Import for type hints (avoiding circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.deal import Deal
    from app.models.listing_mediator import ListingMediator


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    # Auth fields
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Role & Status
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.BUYER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Profile fields
    username: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)

    # Stats
    rating: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.0,
        nullable=False
    )  # 0.00-5.00
    total_deals_as_buyer: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    total_deals_as_seller: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    completed_deals: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(
        "Listing",
        back_populates="seller",
        cascade="all, delete-orphan"
    )
    deals_as_buyer: Mapped[list["Deal"]] = relationship(
        "Deal",
        foreign_keys="Deal.buyer_id",
        back_populates="buyer"
    )
    deals_as_seller: Mapped[list["Deal"]] = relationship(
        "Deal",
        foreign_keys="Deal.seller_id",
        back_populates="seller"
    )
    listings_to_mediate: Mapped[list["ListingMediator"]] = relationship(
        "ListingMediator",
        back_populates="mediator",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, role={self.role})>"
