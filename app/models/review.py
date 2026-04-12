"""
Review model for user reviews.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.deal import Deal


class Review(Base):
    """
    User reviews for mediators/sellers.

    Represents reviews left by users after transactions.
    """

    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    reviewee_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    deal_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("deals.id"), index=True, nullable=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    reviewer: Mapped["User"] = relationship(
        "User", back_populates="given_reviews", foreign_keys=[reviewer_id]
    )
    reviewee: Mapped["User"] = relationship(
        "User", back_populates="received_reviews", foreign_keys=[reviewee_id]
    )
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="reviews")

    __table_args__ = (
        Index("idx_reviews_reviewee_id", "reviewee_id"),
        Index("idx_reviews_deal_id", "deal_id"),
        Index("idx_reviews_created_at", "created_at"),
    )
