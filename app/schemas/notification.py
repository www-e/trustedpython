"""Notification schemas for API responses and requests."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Notification types."""

    ACCOUNT_UPDATE = "account_update"
    MESSAGE = "message"
    SECURITY_ALERT = "security_alert"
    PURCHASE = "purchase"
    SYSTEM = "system"


class NotificationResponse(BaseModel):
    """Single notification response."""

    id: UUID = Field(..., description="Notification ID")
    title: str = Field(..., description="Notification title")
    description: str = Field(..., description="Notification description/body")
    type: NotificationType = Field(..., description="Notification type")
    is_read: bool = Field(..., description="Whether notification has been read")
    icon: Optional[str] = Field(None, description="Icon identifier for UI")
    action_url: Optional[str] = Field(None, description="Deep link URL for navigation")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional notification data"
    )
    created_at: datetime = Field(..., description="Notification creation timestamp")
    relative_time: str = Field(..., description="Human-readable relative time (e.g., '2h ago')")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    notifications: list[NotificationResponse] = Field(
        default_factory=list, description="List of notifications"
    )
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    unread_count: int = Field(..., description="Total unread notification count")


class MarkReadResponse(BaseModel):
    """Response for marking notification as read."""

    success: bool = Field(True, description="Operation status")
    message: str = Field(..., description="Success message")


class MarkAllReadResponse(BaseModel):
    """Response for marking all notifications as read."""

    success: bool = Field(True, description="Operation status")
    data: Dict[str, int] = Field(..., description="Number of notifications marked as read")


class UnreadCountResponse(BaseModel):
    """Response for unread count query."""

    success: bool = Field(True, description="Operation status")
    data: Dict[str, int] = Field(..., description="Unread notification count")


class NotificationTypeSettings(BaseModel):
    """Settings for a specific notification type."""

    enabled: bool = Field(..., description="Whether this type is enabled")
    push: bool = Field(..., description="Whether to send push notifications")
    email: bool = Field(..., description="Whether to send email notifications")


class NotificationSettingsResponse(BaseModel):
    """User notification settings."""

    push_notifications: bool = Field(..., description="Global push notification setting")
    email_notifications: bool = Field(..., description="Global email notification setting")
    types: Dict[str, NotificationTypeSettings] = Field(
        ..., description="Per-type notification settings"
    )


class UpdateNotificationSettingsRequest(BaseModel):
    """Request to update notification settings."""

    push_notifications: Optional[bool] = Field(
        None, description="Enable/disable push notifications"
    )
    email_notifications: Optional[bool] = Field(
        None, description="Enable/disable email notifications"
    )
    types: Optional[Dict[str, Dict[str, Optional[bool]]]] = Field(
        None, description="Per-type settings (all fields optional)"
    )


class CreateNotificationRequest(BaseModel):
    """Request to create a notification (internal use)."""

    user_id: UUID = Field(..., description="Target user ID")
    title: str = Field(..., description="Notification title", max_length=200)
    description: str = Field(..., description="Notification description")
    type: NotificationType = Field(..., description="Notification type")
    icon: Optional[str] = Field(None, description="Icon identifier", max_length=100)
    action_url: Optional[str] = Field(None, description="Deep link URL", max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")
