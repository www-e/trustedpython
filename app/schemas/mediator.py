"""Mediator schemas."""

from pydantic import BaseModel
from datetime import datetime


class MediatorResponse(BaseModel):
    """Schema for mediator response."""
    id: int
    username: str | None
    avatar_url: str | None
    rating: float
    completed_deals: int
    is_available: bool = True

    class Config:
        from_attributes = True


class MediatorListResponse(BaseModel):
    """Schema for list of available mediators."""
    mediators: list[MediatorResponse]
    total: int
