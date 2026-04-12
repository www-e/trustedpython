"""Profile-related schemas."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserProfileStats(BaseModel):
    """User profile statistics."""

    completed_deals: int = Field(..., ge=0, description="Number of completed deals")
    rating: float = Field(..., ge=0, le=5, description="Average rating (0-5)")
    accounts_sold: int = Field(..., ge=0, description="Number of accounts sold")
    bought_count: int = Field(..., ge=0, description="Number of accounts bought")


class UserProfileResponse(BaseModel):
    """Full user profile response."""

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    user_role: str = Field(..., description="User role (e.g., Pro Trader)")
    is_verified: bool = Field(..., description="Verification status")
    member_since: date = Field(..., description="Member since date")
    stats: UserProfileStats = Field(..., description="User statistics")
    recent_listings: Optional[List["ListingSummary"]] = Field(
        default_factory=list, description="Recent listings"
    )
    recent_trades: Optional[List["TradeHistoryItem"]] = Field(
        default_factory=list, description="Recent trades"
    )


class UserStatsResponse(BaseModel):
    """Detailed user statistics response."""

    completed_deals: int = Field(..., ge=0, description="Number of completed deals")
    rating: float = Field(..., ge=0, le=5, description="Average rating (0-5)")
    accounts_sold: int = Field(..., ge=0, description="Number of accounts sold")
    bought_count: int = Field(..., ge=0, description="Number of accounts bought")
    total_revenue: Optional[float] = Field(None, description="Total revenue from sales")
    avg_deal_value: Optional[float] = Field(None, description="Average deal value")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    response_time_avg: Optional[int] = Field(None, description="Average response time in minutes")
    member_since: date = Field(..., description="Member since date")


class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""

    display_name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Display name"
    )
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$", description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    user_role: Optional[str] = Field(None, max_length=50, description="User role")


class UpdateProfileResponse(BaseModel):
    """Response after updating profile."""

    id: UUID = Field(..., description="User ID")
    display_name: Optional[str] = Field(None, description="Display name")
    phone: Optional[str] = Field(None, description="Phone number")
    bio: Optional[str] = Field(None, description="User bio")
    updated_at: datetime = Field(..., description="Update timestamp")


class UploadAvatarResponse(BaseModel):
    """Response after uploading avatar."""

    avatar_url: str = Field(..., description="Avatar URL")


class PublicProfileResponse(BaseModel):
    """Public user profile (without sensitive data)."""

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    user_role: Optional[str] = Field(None, description="User role")
    is_verified: bool = Field(..., description="Verification status")
    member_since: date = Field(..., description="Member since date")
    stats: UserProfileStats = Field(..., description="User statistics")


class TradeHistoryCounterparty(BaseModel):
    """Counterparty information in trade history."""

    username: str = Field(..., description="Username")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class TradeHistoryItem(BaseModel):
    """Single trade history item."""

    id: UUID = Field(..., description="Deal ID")
    title: str = Field(..., description="Deal title")
    price: float = Field(..., ge=0, description="Deal price")
    status: str = Field(..., description="Deal status (completed, pending, cancelled)")
    timestamp: datetime = Field(..., description="Deal timestamp")
    game: Optional[str] = Field(None, description="Game name")
    counterparty: TradeHistoryCounterparty = Field(..., description="Other party in trade")
    role: str = Field(..., description="User role in trade (buyer, seller)")


class TradeHistoryListResponse(BaseModel):
    """Trade history list response."""

    trades: List[TradeHistoryItem] = Field(..., description="List of trades")
    pagination: dict = Field(..., description="Pagination information")


# Forward references for circular imports
class ListingSummary(BaseModel):
    """Brief listing summary for profile."""

    id: UUID = Field(..., description="Listing ID")
    title: str = Field(..., description="Listing title")
    price: float = Field(..., description="Listing price")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    game: Optional[str] = Field(None, description="Game name")
    status: str = Field(..., description="Listing status")


# Update forward references
UserProfileResponse.model_rebuild()
