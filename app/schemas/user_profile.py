"""User profile schemas."""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    username: str | None = Field(None, min_length=3, max_length=50)
    avatar_url: str | None = Field(None, max_length=500)
    bio: str | None = Field(None, max_length=500)

    @validator('username')
    def username_alphanumeric(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: int
    phone: str
    username: str | None
    avatar_url: str | None
    bio: str | None
    role: str
    is_active: bool
    is_verified: bool
    rating: float
    total_deals_as_buyer: int
    total_deals_as_seller: int
    completed_deals: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicUserProfile(BaseModel):
    """Public user profile (for other users to see)."""
    id: int
    username: str | None
    avatar_url: str | None
    bio: str | None
    rating: float
    completed_deals: int
    is_verified: bool

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""
    total_deals_as_buyer: int
    total_deals_as_seller: int
    completed_deals: int
    rating: float
    active_listings: int
    pending_listings: int
    sold_listings: int
