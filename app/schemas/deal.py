"""Deal schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import DealStatus


class DealBase(BaseModel):
    """Base deal schema."""
    listing_id: int
    buyer_id: int
    seller_id: int
    mediator_id: int | None = None
    price: float = Field(gt=0, description="Price must be greater than 0")


class DealCreate(DealBase):
    """Schema for creating a deal."""
    status: DealStatus = DealStatus.PENDING


class DealUpdate(BaseModel):
    """Schema for updating a deal."""
    status: DealStatus | None = None
    mediator_id: int | None = None


class DealResponse(DealBase):
    """Schema for deal response."""
    id: int
    status: DealStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealListResponse(BaseModel):
    """Schema for paginated deal list."""
    items: list[DealResponse]
    pagination: dict


class DealWithListingResponse(DealResponse):
    """Deal with listing details."""
    listing_title: str | None = None
    listing_game_type: str | None = None
    seller_username: str | None = None
    buyer_username: str | None = None
    mediator_username: str | None = None
