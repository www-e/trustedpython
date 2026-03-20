"""Listing schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

from app.models.enums import ListingStatus, GameType


class ListingImageBase(BaseModel):
    """Base listing image schema."""

    image_url: str = Field(..., max_length=500, description="Image URL")
    caption: Optional[str] = Field(None, max_length=200, description="Image caption")
    sort_order: int = Field(default=0, description="Display order")
    is_primary: bool = Field(default=False, description="Is primary image")


class ListingImageCreate(ListingImageBase):
    """Schema for creating a listing image."""

    pass


class ListingImageResponse(ListingImageBase):
    """Schema for listing image response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int


class ListingBase(BaseModel):
    """Base listing schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Listing title")
    description: str = Field(..., min_length=1, description="Listing description")
    category_id: int = Field(..., description="Category ID")
    game_type: GameType = Field(..., description="Game type")
    level: Optional[int] = Field(None, ge=1, description="Account level")
    rank: Optional[str] = Field(None, max_length=100, description="Account rank")
    server: Optional[str] = Field(None, max_length=100, description="Game server")
    skins_count: Optional[int] = Field(None, ge=0, description="Number of skins")
    characters_count: Optional[int] = Field(None, ge=0, description="Number of characters")
    price: float = Field(..., gt=0, description="Listing price")
    is_featured: bool = Field(default=False, description="Is featured listing")


class ListingCreate(ListingBase):
    """Schema for creating a new listing."""

    images: Optional[List[ListingImageCreate]] = Field(
        default=[],
        description="Listing images"
    )


class ListingUpdate(BaseModel):
    """Schema for updating a listing."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    game_type: Optional[GameType] = None
    level: Optional[int] = Field(None, ge=1)
    rank: Optional[str] = Field(None, max_length=100)
    server: Optional[str] = Field(None, max_length=100)
    skins_count: Optional[int] = Field(None, ge=0)
    characters_count: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    status: Optional[ListingStatus] = None
    is_featured: Optional[bool] = None


class ListingResponse(ListingBase):
    """Schema for listing response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    seller_id: int
    status: ListingStatus
    views_count: int
    created_at: datetime
    updated_at: datetime
    images: List[ListingImageResponse] = []


class ListingListResponse(BaseModel):
    """Schema for listing list response."""

    listings: List[ListingResponse]
    total: int
    page: int
    page_size: int


class CategoryListResponse(BaseModel):
    """Schema for category list response."""

    categories: List
    total: int
