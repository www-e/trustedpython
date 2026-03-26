"""Exclusive Card model for home screen promotional content."""

from datetime import datetime
from sqlalchemy import Boolean, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ExclusiveCard(BaseModel):
    """Exclusive card model for home screen promotions.

    Admin-created promotional cards that appear in the exclusive section
    of the home screen with customizable backgrounds, buttons, and tags.
    """

    __tablename__ = "exclusive_cards"

    # Card Content
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Main header text displayed on the card"
    )
    tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tag label (e.g., 'Daily Fire', 'Exclusive')"
    )

    # Button Configuration
    button_text: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Text displayed on the call-to-action button"
    )
    button_link: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="URL or route to navigate when button is clicked"
    )

    # Background Configuration
    background_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type of background: 'image' or 'gradient'"
    )
    background_value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Image URL or CSS gradient value"
    )

    # Display Control
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the card is currently visible"
    )
    order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Display order for sorting (lower values appear first)"
    )
    display_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional expiration date after which card is hidden"
    )

    def __repr__(self) -> str:
        return f"<ExclusiveCard(id={self.id}, title={self.title}, is_active={self.is_active})>"
