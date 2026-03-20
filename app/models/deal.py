"""Deal model for transactions."""

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.base import BaseModel
from app.models.enums import DealStatus

# Import for type hints (avoiding circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class Deal(BaseModel):
    """Deal/transaction between buyer and seller."""

    __tablename__ = "deals"

    # Foreign Keys
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mediator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Deal Details
    status: Mapped[DealStatus] = mapped_column(
        PgEnum(DealStatus, name="deal_status", create_type=False),
        default=DealStatus.PENDING,
        nullable=False,
        index=True
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing")
    buyer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[buyer_id],
        back_populates="deals_as_buyer"
    )
    seller: Mapped["User"] = relationship(
        "User",
        foreign_keys=[seller_id],
        back_populates="deals_as_seller"
    )
    mediator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[mediator_id]
    )

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, status={self.status}, price={self.price})>"
