"""
Listing-related schemas for request/response validation.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateListingRequest(BaseModel):
    """Request schema for creating a new listing."""

    title: str = Field(..., min_length=3, max_length=100, description="Listing title")
    price: float = Field(..., gt=0, description="Listing price (must be > 0)")
    game: str = Field(..., min_length=1, max_length=100, description="Game name")
    category_id: UUID = Field(..., description="Category UUID")
    description: Optional[str] = Field(None, max_length=2000, description="Listing description")
    image_ids: List[UUID] = Field(default_factory=list, description="Uploaded image IDs")
    is_premium: bool = Field(default=False, description="Premium listing status")
    tier: Optional[str] = Field(None, pattern="^(Regular|Gold|Elite)$", description="Premium tier")

    @field_validator("image_ids")
    @classmethod
    def validate_images(cls, v: list[UUID], info: Any) -> list[UUID]:
        """Validate that at least one image is provided."""
        if not v or len(v) == 0:
            raise ValueError("At least one image is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 images allowed")
        return v


class UpdateListingRequest(BaseModel):
    """Request schema for updating an existing listing."""

    title: Optional[str] = Field(None, min_length=3, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    game: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=2000)
    image_ids: Optional[List[UUID]] = None
    is_premium: Optional[bool] = None
    tier: Optional[str] = Field(None, pattern="^(Regular|Gold|Elite)$")

    @field_validator("image_ids")
    @classmethod
    def validate_images(cls, v: Optional[list[UUID]]) -> Optional[list[UUID]]:
        """Validate image count."""
        if v is not None and len(v) > 10:
            raise ValueError("Maximum 10 images allowed")
        return v


class ImageResponse(BaseModel):
    """Response schema for uploaded image."""

    id: UUID = Field(..., description="Image UUID")
    url: str = Field(..., description="Full-size image URL")
    thumbnail_url: str = Field(..., description="Thumbnail image URL")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")


class ListingResponse(BaseModel):
    """Response schema for listing data."""

    id: UUID = Field(..., description="Listing UUID")
    title: str = Field(..., description="Listing title")
    price: float = Field(..., description="Listing price")
    game: str = Field(..., description="Game name")
    category_id: Optional[UUID] = Field(None, description="Category UUID")
    description: Optional[str] = Field(None, description="Listing description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    image_urls: List[str] = Field(default_factory=list, description="Full-size image URLs")
    status: str = Field(..., description="Listing status (draft, active, sold, expired)")
    is_premium: bool = Field(..., description="Premium listing status")
    tier: Optional[str] = Field(None, description="Premium tier")
    created_at: datetime = Field(..., description="Creation timestamp")
    views_count: int = Field(0, description="View count")

    class Config:
        from_attributes = True


class ListingDetailResponse(ListingResponse):
    """Extended response schema for listing details."""

    published_at: Optional[datetime] = Field(None, description="Publish timestamp")
    expired_at: Optional[datetime] = Field(None, description="Expiry timestamp")
    seller_id: UUID = Field(..., description="Seller UUID")
    seller_name: str = Field(..., description="Seller username")
    seller_avatar: Optional[str] = Field(None, description="Seller avatar URL")
    seller_rating: float = Field(..., description="Seller rating")


class PreviewListingRequest(BaseModel):
    """Request schema for previewing a listing."""

    title: str = Field(..., min_length=3, max_length=100)
    price: float = Field(..., gt=0)
    game: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    image_urls: List[str] = Field(default_factory=list)
    is_premium: bool = Field(default=False)
    tier: Optional[str] = Field(None, pattern="^(Regular|Gold|Elite)$")


class PreviewListingData(BaseModel):
    """Preview listing data."""

    title: str
    price: float
    formatted_price: str
    game: str
    thumbnail_url: Optional[str]
    is_premium: bool
    tier: Optional[str]
    estimated_views: Optional[int]


class PreviewListingResponse(BaseModel):
    """Response schema for listing preview."""

    preview: PreviewListingData


class CategoryResponse(BaseModel):
    """Response schema for category."""

    id: UUID = Field(..., description="Category UUID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL slug")
    icon: Optional[str] = Field(None, description="Icon identifier")
    game: Optional[str] = Field(None, description="Associated game")
    description: Optional[str] = Field(None, description="Category description")
    listing_count: int = Field(..., description="Number of listings in category")

    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    """Response schema for game."""

    id: UUID = Field(..., description="Game UUID")
    name: str = Field(..., description="Game name")
    slug: str = Field(..., description="URL slug")
    icon_url: Optional[str] = Field(None, description="Icon image URL")
    banner_url: Optional[str] = Field(None, description="Banner image URL")
    active_listings: int = Field(..., description="Number of active listings")
    avg_price: Optional[float] = Field(None, description="Average listing price")
    popular: bool = Field(..., description="Is popular game")

    class Config:
        from_attributes = True


class RecentActivity(BaseModel):
    """Recent activity item."""

    type: str = Field(..., description="Activity type (view, inquiry, sale)")
    listing_id: UUID = Field(..., description="Listing UUID")
    listing_title: str = Field(..., description="Listing title")
    timestamp: datetime = Field(..., description="Activity timestamp")


class TopPerformingListing(BaseModel):
    """Top performing listing data."""

    id: UUID = Field(..., description="Listing UUID")
    title: str = Field(..., description="Listing title")
    views: int = Field(..., description="View count")
    sold_in_days: Optional[int] = Field(None, description="Days to sell")


class SellAnalyticsData(BaseModel):
    """Sell analytics data."""

    total_listings: int = Field(..., description="Total listings created")
    active_listings: int = Field(..., description="Currently active listings")
    sold_listings: int = Field(..., description="Total sold listings")
    total_views: int = Field(..., description="Total views across all listings")
    total_revenue: float = Field(..., description="Total revenue from sales")
    avg_time_to_sell: Optional[float] = Field(None, description="Average days to sell")
    top_performing_listing: Optional[TopPerformingListing] = Field(None)
    recent_activity: List[RecentActivity] = Field(default_factory=list)


class SellAnalyticsResponse(BaseModel):
    """Response schema for sell analytics."""

    analytics: SellAnalyticsData


class PublishResponse(BaseModel):
    """Response schema for publish/unpublish operations."""

    id: UUID = Field(..., description="Listing UUID")
    status: str = Field(..., description="New listing status")
    published_at: Optional[datetime] = Field(None, description="Publish timestamp")
    unpublished_at: Optional[datetime] = Field(None, description="Unpublish timestamp")


# Profile-specific listing schemas
class UserListingResponse(BaseModel):
    """User listing response for profile module (summary)."""

    id: UUID = Field(..., description="Listing ID")
    title: str = Field(..., description="Listing title")
    price: float = Field(..., description="Listing price")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    game: Optional[str] = Field(None, description="Game name")
    status: str = Field(..., description="Listing status (active, sold, expired)")
    views_count: int = Field(default=0, description="Number of views")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class UserListingDetailResponse(BaseModel):
    """Detailed user listing response for profile module."""

    id: UUID = Field(..., description="Listing ID")
    title: str = Field(..., description="Listing title")
    price: float = Field(..., description="Listing price")
    game: Optional[str] = Field(None, description="Game name")
    description: Optional[str] = Field(None, description="Listing description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    image_urls: List[str] = Field(default_factory=list, description="Additional image URLs")
    status: str = Field(..., description="Listing status (active, sold, expired)")
    is_premium: bool = Field(..., description="Premium listing status")
    tier: Optional[str] = Field(None, description="Listing tier (Regular, Gold, Elite)")
    views_count: int = Field(default=0, description="Number of views")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ProfileCreateListingRequest(BaseModel):
    """Request to create a new listing from profile."""

    title: str = Field(..., min_length=5, max_length=200, description="Listing title")
    price: float = Field(..., gt=0, description="Listing price")
    game: str = Field(..., min_length=2, max_length=100, description="Game name")
    description: Optional[str] = Field(None, max_length=2000, description="Listing description")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Thumbnail URL")
    image_urls: List[str] = Field(default_factory=list, description="Additional image URLs")
    is_premium: bool = Field(default=False, description="Premium listing")
    tier: Optional[str] = Field(None, description="Listing tier")


class ProfileUpdateListingRequest(BaseModel):
    """Request to update a listing from profile."""

    title: Optional[str] = Field(None, min_length=5, max_length=200, description="Listing title")
    price: Optional[float] = Field(None, gt=0, description="Listing price")
    game: Optional[str] = Field(None, min_length=2, max_length=100, description="Game name")
    description: Optional[str] = Field(None, max_length=2000, description="Listing description")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Thumbnail URL")
    image_urls: Optional[List[str]] = Field(None, description="Additional image URLs")
    is_premium: Optional[bool] = Field(None, description="Premium listing")
    tier: Optional[str] = Field(None, description="Listing tier")


class UpdateListingStatusRequest(BaseModel):
    """Request to update listing status."""

    status: str = Field(..., description="New status (active, sold, expired)")


class UploadImageResponse(BaseModel):
    """Response after uploading listing image."""

    id: str = Field(..., description="Image ID")
    url: str = Field(..., description="Image URL")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., ge=0, description="File size in bytes")


class UserListingsListResponse(BaseModel):
    """User listings list response."""

    listings: List[UserListingResponse] = Field(..., description="List of listings")
    pagination: dict = Field(..., description="Pagination information")
