"""Account-related schemas for the Buy Flow."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import UUID4, BaseModel, Field


class AccountFeatureSchema(BaseModel):
    """Account feature schema."""

    icon: str = Field(..., description="Icon identifier for the feature")
    label: str = Field(..., description="Feature label/text")

    model_config = {"from_attributes": True}


class SellerInfoSchema(BaseModel):
    """Seller information in account response."""

    id: str = Field(..., description="Seller user ID")
    username: str = Field(..., description="Seller username")
    display_name: Optional[str] = Field(None, description="Seller display name")
    avatar_url: Optional[str] = Field(None, description="Seller avatar URL")
    is_online: bool = Field(False, description="Whether seller is online")
    rating: float = Field(..., ge=0, le=5, description="Seller rating")
    total_sales: int = Field(..., ge=0, description="Total number of sales")
    member_since: datetime = Field(..., description="Seller registration date")

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    """Account response for browse/list views."""

    id: str = Field(..., description="Account ID")
    title: str = Field(..., description="Account title")
    game: str = Field(..., description="Game name")
    rank: Optional[str] = Field(None, description="Account rank/level")
    price: float = Field(..., ge=0, description="Account price")
    currency: str = Field("EGP", description="Currency code (default: EGP)")
    seller_id: str = Field(..., description="Seller user ID")
    seller_name: str = Field(..., description="Seller username")
    seller_avatar: Optional[str] = Field(None, description="Seller avatar URL")
    rating: float = Field(..., ge=0, le=5, description="Account rating")
    reviews_count: int = Field(..., ge=0, description="Number of reviews")
    description: str = Field(..., description="Account description")
    images: List[str] = Field(default_factory=list, description="Account image URLs")
    features: List[AccountFeatureSchema] = Field(
        default_factory=list, description="Account features/highlights"
    )
    is_verified: bool = Field(False, description="Whether account is verified")
    is_featured: bool = Field(False, description="Whether account is featured")
    created_at: datetime = Field(..., description="Listing creation date")

    model_config = {"from_attributes": True}


class AccountDetailResponse(BaseModel):
    """Detailed account response with full seller info."""

    id: str = Field(..., description="Account ID")
    title: str = Field(..., description="Account title")
    game: str = Field(..., description="Game name")
    rank: Optional[str] = Field(None, description="Account rank/level")
    price: float = Field(..., ge=0, description="Account price")
    currency: str = Field("EGP", description="Currency code")
    seller: SellerInfoSchema = Field(..., description="Seller information")
    rating: float = Field(..., ge=0, le=5, description="Account rating")
    reviews_count: int = Field(..., ge=0, description="Number of reviews")
    description: str = Field(..., description="Account description")
    images: List[str] = Field(default_factory=list, description="Account image URLs")
    features: List[AccountFeatureSchema] = Field(
        default_factory=list, description="Account features/highlights"
    )
    is_verified: bool = Field(False, description="Whether account is verified")
    is_featured: bool = Field(False, description="Whether account is featured")
    is_available: bool = Field(True, description="Whether account is available")
    created_at: datetime = Field(..., description="Listing creation date")
    updated_at: datetime = Field(..., description="Last update date")

    model_config = {"from_attributes": True}


class PriceRangeSchema(BaseModel):
    """Price range filter option."""

    label: str = Field(..., description="Display label for price range")
    min: Optional[float] = Field(None, description="Minimum price")
    max: Optional[float] = Field(None, description="Maximum price")


class AccountFiltersSchema(BaseModel):
    """Available filters for account browsing."""

    available_games: List[str] = Field(default_factory=list, description="List of available games")
    price_ranges: List[PriceRangeSchema] = Field(
        default_factory=list, description="Available price range filters"
    )
    available_levels: List[str] = Field(
        default_factory=list, description="Available rank/level filters"
    )


class AccountsBrowseResponse(BaseModel):
    """Response for browse accounts endpoint."""

    accounts: List[AccountResponse] = Field(..., description="List of accounts")
    filters: AccountFiltersSchema = Field(..., description="Available filters")
    pagination: dict = Field(..., description="Pagination information")


class SimilarAccountsResponse(BaseModel):
    """Response for similar accounts endpoint."""

    accounts: List[AccountResponse] = Field(
        default_factory=list, description="List of similar accounts"
    )
