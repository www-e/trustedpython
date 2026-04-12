"""
Notification preferences and settings service.

This module handles all notification preference operations, including
getting and updating user notification settings, both global and
per-notification-type settings.
"""

import logging
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import NotificationSettingsResponse, NotificationTypeSettings

logger = logging.getLogger(__name__)


class NotificationPreferencesService:
    """
    Service for notification preference management.

    Provides methods for retrieving and updating user notification
    preferences, including global settings (push, email) and
    per-type settings for different notification categories.
    """

    @staticmethod
    async def get_notification_settings(
        db: AsyncSession, user_id: UUID
    ) -> NotificationSettingsResponse:
        """
        Get notification preferences for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            NotificationSettingsResponse: User's notification settings
        """
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        preference = result.scalar_one_or_none()

        # Create default preferences if none exist
        if not preference:
            preference = NotificationPreference(
                user_id=user_id,
                push_notifications=True,
                email_notifications=True,
                types={
                    "account_update": {"enabled": True, "push": True, "email": True},
                    "message": {"enabled": True, "push": True, "email": True},
                    "security_alert": {"enabled": True, "push": True, "email": True},
                    "purchase": {"enabled": True, "push": True, "email": True},
                    "system": {"enabled": True, "push": True, "email": True},
                },
            )
            db.add(preference)
            await db.commit()

        # Convert types dict to proper format
        types_dict = {}
        for type_name, settings in preference.types.items():
            types_dict[type_name] = NotificationTypeSettings(**settings)

        return NotificationSettingsResponse(
            push_notifications=preference.push_notifications,
            email_notifications=preference.email_notifications,
            types=types_dict,
        )

    @staticmethod
    async def update_notification_settings(
        db: AsyncSession,
        user_id: UUID,
        push_notifications: Optional[bool] = None,
        email_notifications: Optional[bool] = None,
        types: Optional[Dict[str, Dict[str, Optional[bool]]]] = None,
    ) -> NotificationSettingsResponse:
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
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        preference = result.scalar_one_or_none()

        # Create default if none exists
        if not preference:
            preference = NotificationPreference(
                user_id=user_id,
                push_notifications=True,
                email_notifications=True,
                types={
                    "account_update": {"enabled": True, "push": True, "email": True},
                    "message": {"enabled": True, "push": True, "email": True},
                    "security_alert": {"enabled": True, "push": True, "email": True},
                    "purchase": {"enabled": True, "push": True, "email": True},
                    "system": {"enabled": True, "push": True, "email": True},
                },
            )
            db.add(preference)

        # Update settings if provided
        if push_notifications is not None:
            preference.push_notifications = push_notifications

        if email_notifications is not None:
            preference.email_notifications = email_notifications

        if types:
            for type_name, settings in types.items():
                if type_name in preference.types:
                    for key, value in settings.items():
                        if value is not None:
                            preference.types[type_name][key] = value

        await db.commit()

        return await NotificationPreferencesService.get_notification_settings(db, user_id)

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of unread notifications
        """
        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
        )
        return result.scalar() or 0
