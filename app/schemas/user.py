"""User schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$", description="Phone number")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)"
    )
    role: UserRole = Field(default=UserRole.BUYER, description="User role")


class UserLogin(BaseModel):
    """Schema for user login."""

    phone: str = Field(..., description="Phone number")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    role: UserRole
    is_active: bool
    is_verified: bool
