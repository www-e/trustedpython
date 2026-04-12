"""
Notification services package.

Provides specialized notification services for notification management.
This package maintains backward compatibility through the NotificationService facade.

Usage:
    # Direct import (recommended for new code):
    from app.services.notifications import NotificationCrudService, NotificationPreferencesService

    # Facade import (for backward compatibility):
    from app.services.notifications import NotificationService
"""

from typing import Any, Dict, Optional
from uuid import UUID

from app.services.notifications.crud_service import NotificationCrudService
from app.services.notifications.preferences_service import NotificationPreferencesService

__all__ = [
    "NotificationCrudService",
    "NotificationPreferencesService",
    "NotificationService",  # Facade for backward compatibility
]


# Backward compatibility facade
class NotificationService:
    """
    Facade for backward compatibility with legacy NotificationService.

    This class provides the same interface as the original monolithic
    NotificationService by delegating to specialized service modules.
    All methods are static and match the original API exactly.

    Deprecated: Import specific services directly instead.
    """

    @staticmethod
    async def get_user_notifications(
        db: Any,
        user_id: UUID,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """
        Get paginated notifications for a user.

        Args:
            db: Database session
            user_id: User ID
            notification_type: Filter by notification type
            is_read: Filter by read status
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            NotificationListResponse: Paginated notifications
        """
        return await NotificationCrudService.get_user_notifications(
            db, user_id, notification_type, is_read, page, limit
        )

    @staticmethod
    async def get_notification(db: Any, notification_id: UUID, user_id: UUID) -> Any:
        """
        Get a single notification by ID.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            NotificationResponse: Notification data
        """
        return await NotificationCrudService.get_notification(db, notification_id, user_id)

    @staticmethod
    async def mark_as_read(db: Any, notification_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Mark a notification as read.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Dict with success status and message
        """
        return await NotificationCrudService.mark_as_read(db, notification_id, user_id)

    @staticmethod
    async def mark_all_as_read(db: Any, user_id: UUID) -> Dict[str, Any]:
        """
        Mark all unread notifications as read for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dict with success status and count of marked notifications
        """
        return await NotificationCrudService.mark_all_as_read(db, user_id)

    @staticmethod
    async def get_unread_count(db: Any, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of unread notifications
        """
        return await NotificationPreferencesService.get_unread_count(db, user_id)

    @staticmethod
    async def delete_notification(db: Any, notification_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Delete a notification.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Dict with success status and message
        """
        return await NotificationCrudService.delete_notification(db, notification_id, user_id)

    @staticmethod
    async def get_notification_settings(db: Any, user_id: UUID) -> Any:
        """
        Get notification preferences for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            NotificationSettingsResponse: User's notification settings
        """
        return await NotificationPreferencesService.get_notification_settings(db, user_id)

    @staticmethod
    async def update_notification_settings(
        db: Any,
        user_id: UUID,
        push_notifications: Optional[bool] = None,
        email_notifications: Optional[bool] = None,
        types: Optional[Any] = None,
    ) -> Any:
        """
        Update notification preferences for a user.

        Args:
            db: Database session
            user_id: User ID
            push_notifications: New push notification setting
            email_notifications: New email notification setting
            types: New per-type settings

        Returns:
            NotificationSettingsResponse: Updated settings
        """
        return await NotificationPreferencesService.update_notification_settings(
            db, user_id, push_notifications, email_notifications, types
        )

    @staticmethod
    async def create_notification(
        db: Any,
        user_id: UUID,
        title: str,
        description: str,
        notification_type: Any,
        icon: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Create a new notification for a user.

        Args:
            db: Database session
            user_id: Target user ID
            title: Notification title
            description: Notification description
            notification_type: Type of notification
            icon: Icon identifier (auto-selected if None)
            action_url: Deep link URL
            metadata: Additional data

        Returns:
            NotificationResponse: Created notification
        """
        return await NotificationCrudService.create_notification(
            db, user_id, title, description, notification_type, icon, action_url, metadata
        )

    @staticmethod
    async def send_push_notification(user_id: UUID, notification: Any) -> None:
        """
        Send push notification via Redis pub/sub.

        Args:
            user_id: Target user ID
            notification: Notification to send
        """
        from app.services.notifications.base import send_push_notification

        await send_push_notification(user_id, notification)
