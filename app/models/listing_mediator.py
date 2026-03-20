"""Listing-Mediator relationship model."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Import for type hints (avoiding circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class ListingMediator(BaseModel):
    """Which mediators are allowed to mediate a listing."""

    __tablename__ = "listing_mediators"

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False
    )
    mediator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(
        "Listing",
        back_populates="allowed_mediators"
    )
    mediator: Mapped["User"] = relationship(
        "User",
        back_populates="listings_to_mediate"
    )

    __table_args__ = (
        UniqueConstraint('listing_id', 'mediator_id', name='unique_listing_mediator'),
    )

    def __repr__(self) -> str:
        return f"<ListingMediator(listing_id={self.listing_id}, mediator_id={self.mediator_id})>"
