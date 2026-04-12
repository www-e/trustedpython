"""
Authentication request and response schemas.

Defines all schemas for authentication endpoints including registration,
login, password reset, and token refresh operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """
    User registration request schema.

    Attributes:
        username: Unique username (3-50 characters, alphanumeric + underscore)
        email: Valid email address
        phone: Phone number (10+ digits)
        password: Password (6+ characters)

    Example:
        >>> register = RegisterRequest(
        ...     username="gamer123",
        ...     email="user@example.com",
        ...     phone="1234567890",
        ...     password="SecurePass123"
        ... )
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        description="Unique username (3-50 characters, alphanumeric + underscore)",
    )
    email: EmailStr = Field(..., description="Valid email address")
    phone: str = Field(
        ..., min_length=10, pattern="^[0-9]+$", description="Phone number (10+ digits)"
    )
    password: str = Field(..., min_length=6, max_length=100, description="Password (6+ characters)")


class LoginRequest(BaseModel):
    """
    User login request schema.

    Attributes:
        username: Username or email
        password: User password

    Example:
        >>> login = LoginRequest(
        ...     username="gamer123",
        ...     password="SecurePass123"
        ... )
    """

    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="User password")


class ForgotPasswordRequest(BaseModel):
    """
    Password reset request schema.

    Attributes:
        email: Email address for password reset

    Example:
        >>> forgot = ForgotPasswordRequest(email="user@example.com")
    """

    email: EmailStr = Field(..., description="Email address for password reset")


class ResetPasswordRequest(BaseModel):
    """
    Password reset confirmation schema.

    Attributes:
        token: Password reset token from email
        new_password: New password (6+ characters)

    Example:
        >>> reset = ResetPasswordRequest(
        ...     token="reset_token_here",
        ...     new_password="NewSecurePass123"
        ... )
    """

    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(
        ..., min_length=6, max_length=100, description="New password (6+ characters)"
    )


class RefreshTokenRequest(BaseModel):
    """
    Token refresh request schema.

    Attributes:
        refresh_token: Valid refresh token

    Example:
        >>> refresh = RefreshTokenRequest(refresh_token="refresh_token_here")
    """

    refresh_token: str = Field(..., description="Valid refresh token")


class VerifyEmailRequest(BaseModel):
    """
    Email verification request schema.

    Attributes:
        token: Email verification token from email

    Example:
        >>> verify = VerifyEmailRequest(token="verify_token_here")
    """

    token: str = Field(..., description="Email verification token from email")


# Response Schemas


class UserResponse(BaseModel):
    """
    Basic user information response.

    Attributes:
        id: User UUID
        username: Username
        email: Email address
        phone: Phone number
        display_name: Display name (optional)
        created_at: Account creation timestamp
    """

    id: UUID
    username: str
    email: str
    phone: str
    display_name: Optional[str] = None
    created_at: datetime


class UserStats(BaseModel):
    """
    User statistics for profile response.

    Attributes:
        total_sales: Number of successful sales
        total_purchases: Number of successful purchases
        rating: Average rating (0-5)
        reviews_count: Total number of reviews received
    """

    total_sales: int = 0
    total_purchases: int = 0
    rating: float = 0.0
    reviews_count: int = 0


class CurrentUserResponse(BaseModel):
    """
    Complete current user profile response.

    Attributes:
        id: User UUID
        username: Username
        email: Email address
        phone: Phone number
        display_name: Display name
        avatar_url: Profile image URL
        is_verified: Verification status
        created_at: Account creation timestamp
        stats: User statistics
    """

    id: UUID
    username: str
    email: str
    phone: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    created_at: datetime
    stats: UserStats


class TokenResponse(BaseModel):
    """
    JWT token response.

    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token
        expires_in: Access token expiration in seconds
    """

    access_token: str
    refresh_token: str
    expires_in: int


class RegisterResponse(BaseModel):
    """
    Registration response with user and tokens.

    Attributes:
        user: Created user information
        access_token: JWT access token
        refresh_token: JWT refresh token
        expires_in: Access token expiration in seconds
    """

    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int


class LoginResponse(BaseModel):
    """
    Login response with user and tokens.

    Attributes:
        user: Authenticated user information
        access_token: JWT access token
        refresh_token: JWT refresh token
        expires_in: Access token expiration in seconds
    """

    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int
