"""User-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern="^[a-zA-Z0-9_]+$",
        description="Unique username (alphanumeric and underscore only)",
    )
    email: EmailStr = Field(..., description="User email address")
    phone: Optional[str] = Field(
        None, pattern=r"^\+?[1-9]\d{1,14}$", description="Phone number in E.164 format"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ..., min_length=8, max_length=100, description="User password (min 8 characters)"
    )
    display_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Display name (optional, defaults to username)",
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    phone: Optional[str] = Field(
        None, pattern=r"^\+?[1-9]\d{1,14}$", description="Phone number in E.164 format"
    )
    display_name: Optional[str] = Field(
        None, min_length=2, max_length=50, description="Display name"
    )
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL to user avatar image")


class UserResponse(BaseModel):
    """Schema for user response (public information)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_verified: bool = Field(..., description="Whether the user is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserStatsSchema(BaseModel):
    """User statistics schema."""

    completed_deals: int = Field(..., ge=0, description="Number of completed deals")
    rating: float = Field(..., ge=0, le=5, description="Average rating (0-5)")
    accounts_sold: int = Field(..., ge=0, description="Number of accounts sold")
    bought_count: int = Field(..., ge=0, description="Number of accounts bought")
    response_rate: Optional[float] = Field(
        None, ge=0, le=100, description="Response rate percentage"
    )
    avg_response_time: Optional[int] = Field(
        None, ge=0, description="Average response time in minutes"
    )


class UserWithStatsResponse(UserResponse):
    """Schema for user response with statistics."""

    stats: UserStatsSchema = Field(..., description="User statistics")


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Schema for login response."""

    user: UserResponse = Field(..., description="Authenticated user information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field("bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Schema for token refresh response."""

    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field("bearer", description="Token type")


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password (min 8 characters)"
    )


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="Email address for password reset")


class ConfirmResetPasswordRequest(BaseModel):
    """Schema for confirming password reset."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password (min 8 characters)"
    )


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""

    token: str = Field(..., description="Email verification token")
