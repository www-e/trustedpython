"""Deal-related schemas for the Buy Flow."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel, Field


class DealStatus(str, Enum):
    """Deal status values."""

    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_SUBMITTED = "payment_submitted"
    VERIFIED = "verified"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class PaymentStatus(str, Enum):
    """Payment status values."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class CreateDealRequest(BaseModel):
    """Request schema for creating a deal."""

    account_id: str = Field(..., description="Account ID to purchase")
    mediator_id: str = Field(..., description="Mediator ID for the transaction")
    quantity: int = Field(default=1, ge=1, le=99, description="Quantity (default: 1)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes for the deal")


class AccountSummarySchema(BaseModel):
    """Account summary in deal response."""

    id: str = Field(..., description="Account ID")
    title: str = Field(..., description="Account title")
    price: float = Field(..., ge=0, description="Account price")
    game: str = Field(..., description="Game name")

    model_config = {"from_attributes": True}


class AccountFullSchema(BaseModel):
    """Full account in deal detail response."""

    id: str = Field(..., description="Account ID")
    title: str = Field(..., description="Account title")
    game: str = Field(..., description="Game name")
    price: float = Field(..., ge=0, description="Account price")
    images: List[str] = Field(default_factory=list, description="Account images")

    model_config = {"from_attributes": True}


class MediatorSummarySchema(BaseModel):
    """Mediator summary in deal response."""

    id: str = Field(..., description="Mediator ID")
    name: str = Field(..., description="Mediator name")
    avatar: str = Field(..., description="Mediator avatar URL")
    rating: Optional[float] = Field(None, description="Mediator rating")

    model_config = {"from_attributes": True}


class UserSummarySchema(BaseModel):
    """User summary in deal response."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")

    model_config = {"from_attributes": True}


class PaymentInfoSchema(BaseModel):
    """Payment information in deal response."""

    status: PaymentStatus = Field(..., description="Payment status")
    screenshot_url: Optional[str] = Field(None, description="Payment screenshot URL")
    submitted_at: Optional[datetime] = Field(None, description="Payment submission date")
    verified_at: Optional[datetime] = Field(None, description="Payment verification date")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason if rejected")

    model_config = {"from_attributes": True}


class DealResponse(BaseModel):
    """Deal response for created deals."""

    id: str = Field(..., description="Deal ID")
    status: DealStatus = Field(..., description="Deal status")
    account: AccountSummarySchema = Field(..., description="Account summary")
    mediator: MediatorSummarySchema = Field(..., description="Mediator summary")
    buyer_id: str = Field(..., description="Buyer user ID")
    seller_id: str = Field(..., description="Seller user ID")
    total_amount: float = Field(..., ge=0, description="Total deal amount")
    created_at: datetime = Field(..., description="Deal creation date")
    chat_room_id: str = Field(..., description="Associated chat room ID")

    model_config = {"from_attributes": True}


class DealDetailResponse(BaseModel):
    """Detailed deal response."""

    id: str = Field(..., description="Deal ID")
    status: DealStatus = Field(..., description="Deal status")
    account: AccountFullSchema = Field(..., description="Account details")
    mediator: MediatorSummarySchema = Field(..., description="Mediator details")
    buyer: UserSummarySchema = Field(..., description="Buyer details")
    seller: UserSummarySchema = Field(..., description="Seller details")
    total_amount: float = Field(..., ge=0, description="Total deal amount")
    payment: Optional[PaymentInfoSchema] = Field(None, description="Payment information")
    chat_room_id: str = Field(..., description="Associated chat room ID")
    created_at: datetime = Field(..., description="Deal creation date")
    updated_at: datetime = Field(..., description="Last update date")
    completed_at: Optional[datetime] = Field(None, description="Deal completion date")
    notes: Optional[str] = Field(None, description="Deal notes")

    model_config = {"from_attributes": True}


class UpdateDealStatusRequest(BaseModel):
    """Request schema for updating deal status."""

    status: DealStatus = Field(..., description="New deal status")
    notes: Optional[str] = Field(
        None, max_length=1000, description="Optional notes for status change"
    )


class SubmitPaymentRequest(BaseModel):
    """Request schema for submitting payment (metadata only, file is separate)."""

    notes: Optional[str] = Field(None, max_length=500, description="Optional notes with payment")


class PaymentStatusResponse(BaseModel):
    """Response for payment status endpoints."""

    deal_id: str = Field(..., description="Deal ID")
    status: PaymentStatus = Field(..., description="Payment status")
    screenshot_url: Optional[str] = Field(None, description="Payment screenshot URL")
    submitted_at: Optional[datetime] = Field(None, description="Payment submission date")
    verified_at: Optional[datetime] = Field(None, description="Payment verification date")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason if rejected")

    model_config = {"from_attributes": True}


class ConfirmPaymentRequest(BaseModel):
    """Request schema for confirming payment."""

    notes: Optional[str] = Field(
        None, max_length=500, description="Optional notes with confirmation"
    )


class RejectPaymentRequest(BaseModel):
    """Request schema for rejecting payment."""

    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection")
