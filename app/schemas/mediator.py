"""Mediator-related schemas for the Buy Flow."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MediatorTier(str, Enum):
    """Mediator tier levels."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ELITE = "elite"


class PaymentMethodType(str, Enum):
    """Payment method types."""

    BANK = "bank"
    WALLET = "wallet"
    CRYPTO = "crypto"


class PaymentMethodSchema(BaseModel):
    """Payment method schema."""

    type: PaymentMethodType = Field(..., description="Payment method type")
    name: str = Field(..., description="Payment method name (e.g., Bank Transfer)")
    icon: str = Field(..., description="Icon identifier")
    details: str = Field(..., description="Payment details/instructions")

    model_config = {"from_attributes": True}


class MediatorBadgeSchema(BaseModel):
    """Mediator badge schema."""

    id: str = Field(..., description="Badge ID")
    name: str = Field(..., description="Badge name")
    icon: str = Field(..., description="Badge icon identifier")
    description: str = Field(..., description="Badge description")
    earned_at: datetime = Field(..., description="Badge earned date")

    model_config = {"from_attributes": True}


class MediatorResponse(BaseModel):
    """Mediator response for list views."""

    id: str = Field(..., description="Mediator ID")
    name: str = Field(..., description="Mediator display name")
    avatar: str = Field(..., description="Mediator avatar URL")
    rating: float = Field(..., ge=0, le=5, description="User rating")
    program_rating: float = Field(..., ge=0, le=5, description="Mediator program rating")
    transactions_count: int = Field(..., ge=0, description="Total transactions")
    specialization: str = Field(..., description="Game specialization")
    payment_methods: List[PaymentMethodSchema] = Field(
        default_factory=list, description="Accepted payment methods"
    )
    response_time: str = Field(..., description="Average response time (e.g., '5 min')")
    is_online: bool = Field(False, description="Whether mediator is online")
    tier: MediatorTier = Field(..., description="Mediator tier level")
    is_verified: bool = Field(False, description="Whether mediator is verified")
    badges: List[MediatorBadgeSchema] = Field(
        default_factory=list, description="Mediator badges/achievements"
    )
    bio: str = Field(..., description="Mediator bio/description")

    model_config = {"from_attributes": True}


class MediatorStatsSchema(BaseModel):
    """Mediator statistics."""

    total_deals: int = Field(..., ge=0, description="Total deals mediated")
    successful_deals: int = Field(..., ge=0, description="Successfully completed deals")
    failed_deals: int = Field(..., ge=0, description="Failed deals")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    avg_response_time: float = Field(..., ge=0, description="Average response time in minutes")
    member_since: datetime = Field(..., description="Mediator registration date")


class MediatorDetailResponse(BaseModel):
    """Detailed mediator response."""

    id: str = Field(..., description="Mediator ID")
    name: str = Field(..., description="Mediator display name")
    avatar: str = Field(..., description="Mediator avatar URL")
    rating: float = Field(..., ge=0, le=5, description="User rating")
    program_rating: float = Field(..., ge=0, le=5, description="Mediator program rating")
    transactions_count: int = Field(..., ge=0, description="Total transactions")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    specialization: str = Field(..., description="Game specialization")
    payment_methods: List[PaymentMethodSchema] = Field(
        default_factory=list, description="Accepted payment methods"
    )
    response_time: str = Field(..., description="Average response time")
    is_online: bool = Field(False, description="Whether mediator is online")
    tier: MediatorTier = Field(..., description="Mediator tier level")
    is_verified: bool = Field(False, description="Whether mediator is verified")
    badges: List[MediatorBadgeSchema] = Field(default_factory=list, description="Mediator badges")
    bio: str = Field(..., description="Mediator bio")
    stats: MediatorStatsSchema = Field(..., description="Mediator statistics")

    model_config = {"from_attributes": True}


class MediatorReviewSchema(BaseModel):
    """Mediator review schema."""

    id: str = Field(..., description="Review ID")
    reviewer: dict = Field(..., description="Reviewer info")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comment: str = Field(..., description="Review comment")
    deal_id: str = Field(..., description="Associated deal ID")
    created_at: datetime = Field(..., description="Review date")

    model_config = {"from_attributes": True}


class MediatorReviewsResponse(BaseModel):
    """Response for mediator reviews endpoint."""

    reviews: List[MediatorReviewSchema] = Field(..., description="List of reviews")
    pagination: dict = Field(..., description="Pagination information")
    average_rating: float = Field(..., ge=0, le=5, description="Average rating")


class MediatorFiltersSchema(BaseModel):
    """Available filters for mediator browsing."""

    available_specializations: List[str] = Field(
        default_factory=list, description="Available game specializations"
    )
    available_tiers: List[str] = Field(default_factory=list, description="Available tier filters")
