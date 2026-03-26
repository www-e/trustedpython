"""Exclusive Card schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional


class ExclusiveCardBase(BaseModel):
    """Base exclusive card schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Main header text")
    tag: str = Field(..., min_length=1, max_length=50, description="Tag label")
    button_text: str = Field(..., min_length=1, max_length=100, description="Button text")
    button_link: str = Field(..., min_length=1, max_length=500, description="Button URL/route")
    background_type: str = Field(..., min_length=1, max_length=20, description="Background type")
    background_value: str = Field(..., min_length=1, max_length=500, description="Image URL or gradient")
    is_active: bool = Field(default=True, description="Whether card is visible")
    order: int = Field(default=0, ge=0, description="Display order")
    display_until: Optional[datetime] = Field(None, description="Expiration date")

    @field_validator('background_type')
    @classmethod
    def validate_background_type(cls, v: str) -> str:
        """Validate background_type is either 'image' or 'gradient'."""
        if v not in ['image', 'gradient']:
            raise ValueError("background_type must be 'image' or 'gradient'")
        return v


class ExclusiveCardCreate(ExclusiveCardBase):
    """Schema for creating a new exclusive card."""

    pass


class ExclusiveCardUpdate(BaseModel):
    """Schema for updating an exclusive card."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    tag: Optional[str] = Field(None, min_length=1, max_length=50)
    button_text: Optional[str] = Field(None, min_length=1, max_length=100)
    button_link: Optional[str] = Field(None, min_length=1, max_length=500)
    background_type: Optional[str] = Field(None, min_length=1, max_length=20)
    background_value: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    order: Optional[int] = Field(None, ge=0)
    display_until: Optional[datetime] = None

    @field_validator('background_type')
    @classmethod
    def validate_background_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate background_type if provided."""
        if v is not None and v not in ['image', 'gradient']:
            raise ValueError("background_type must be 'image' or 'gradient'")
        return v


class ExclusiveCardResponse(ExclusiveCardBase):
    """Schema for exclusive card response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
