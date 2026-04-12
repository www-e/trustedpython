"""Notification business logic service."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.redis import get_redis
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    CreateNotificationRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingsResponse,
    NotificationType,
    NotificationTypeSettings,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification management."""

    # Notification type icons mapping
    ICONS = {
        NotificationType.ACCOUNT_UPDATE: "account_circle",
        NotificationType.MESSAGE: "message",
        NotificationType.SECURITY_ALERT: "security",
        NotificationType.PURCHASE: "shopping_cart",
        NotificationType.SYSTEM: "notifications",
    }

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: UUID,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> NotificationListResponse:
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

        Raises:
            ValueError: If page or limit are invalid
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50")

        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        # Apply filters
        if notification_type:
            query = query.where(Notification.type == notification_type)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * limit
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        notifications = result.scalars().all()

        # Get unread count
        unread_count = await NotificationService.get_unread_count(db, user_id)

        # Convert to response format
        notification_responses = []
        for notification in notifications:
            notification_responses.append(
                await NotificationService._notification_to_response(notification)
            )

        # Build pagination metadata
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        pagination = {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

        return NotificationListResponse(
            notifications=notification_responses, pagination=pagination, unread_count=unread_count
        )

    @staticmethod
    async def get_notification(
        db: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> NotificationResponse:
        """
        Get a single notification by ID.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            NotificationResponse: Notification data

        Raises:
            NotFoundException: If notification doesn't exist
            ForbiddenException: If notification belongs to different user
        """
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException("Notification not found")

        if notification.user_id != user_id:
            raise ForbiddenException("Access denied to this notification")

        return await NotificationService._notification_to_response(notification)

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Mark a notification as read.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Dict with success status and message

        Raises:
            NotFoundException: If notification doesn't exist
            ForbiddenException: If notification belongs to different user
        """
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException("Notification not found")

        if notification.user_id != user_id:
            raise ForbiddenException("Access denied to this notification")

        # Mark as read if not already read
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await db.commit()

            # Publish to WebSocket for real-time update
            await NotificationService._publish_notification_update(user_id, notification_id, "read")

        return {"success": True, "message": "Notification marked as read"}

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """
        Mark all unread notifications as read for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dict with success status and count of marked notifications
        """
        # Find all unread notifications
        result = await db.execute(
            select(Notification).where(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
        )
        notifications = result.scalars().all()

        marked_count = len(notifications)

        # Mark all as read
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

        await db.commit()

        # Publish WebSocket event
        await NotificationService._publish_all_read_update(user_id)

        return {"success": True, "data": {"marked_count": marked_count}}

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

    @staticmethod
    async def delete_notification(
        db: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Delete a notification.

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Dict with success status and message

        Raises:
            NotFoundException: If notification doesn't exist
            ForbiddenException: If notification belongs to different user
        """
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException("Notification not found")

        if notification.user_id != user_id:
            raise ForbiddenException("Access denied to this notification")

        await db.delete(notification)
        await db.commit()

        # Publish deletion update
        await NotificationService._publish_notification_update(user_id, notification_id, "deleted")

        return {"success": True, "message": "Notification deleted"}

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

        return await NotificationService.get_notification_settings(db, user_id)

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: UUID,
        title: str,
        description: str,
        notification_type: NotificationType,
        icon: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationResponse:
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

        Raises:
            ValueError: If user doesn't exist
        """
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} does not exist")

        # Get icon for type if not provided
        if not icon:
            icon = NotificationService.ICONS.get(notification_type, "notifications")

        # Create notification
        notification = Notification(
            user_id=user_id,
            title=title,
            description=description,
            type=notification_type.value,
            icon=icon,
            action_url=action_url,
            meta_data=metadata or {},
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Publish to Redis for WebSocket delivery
        await NotificationService._publish_new_notification(notification)

        # Publish badge count update
        await NotificationService._publish_badge_update(user_id)

        return await NotificationService._notification_to_response(notification)

    @staticmethod
    async def send_push_notification(user_id: UUID, notification: Notification) -> None:
        """
        Send push notification via Redis pub/sub.

        Args:
            user_id: Target user ID
            notification: Notification to send
        """
        try:
            redis_client = await get_redis()
            if not redis_client:
                logger.warning("Redis not available for push notification")
                return

            # Publish to user's notification channel
            channel = f"notifications:{user_id}"
            message = {
                "id": str(notification.id),
                "title": notification.title,
                "description": notification.description,
                "type": notification.type,
                "icon": notification.icon,
                "action_url": notification.action_url,
                "metadata": notification.meta_data,
                "created_at": notification.created_at.isoformat(),
            }

            await redis_client.publish(channel, json.dumps(message))
            logger.info(f"Push notification sent to {channel}")

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")

    @staticmethod
    async def _notification_to_response(notification: Notification) -> NotificationResponse:
        """
        Convert notification model to response format.

        Args:
            notification: Notification model

        Returns:
            NotificationResponse: API response format
        """
        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            description=notification.description,
            type=NotificationType(notification.type),
            is_read=notification.is_read,
            icon=notification.icon,
            action_url=notification.action_url,
            metadata=notification.meta_data or {},
            created_at=notification.created_at,
            relative_time=NotificationService._get_relative_time(notification.created_at),
        )

    @staticmethod
    def _get_relative_time(created_at: datetime) -> str:
        """
        Get human-readable relative time string.

        Args:
            created_at: Creation timestamp

        Returns:
            Relative time string (e.g., '2h ago')
        """
        now = datetime.now(timezone.utc)
        delta = now - created_at

        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days}d ago"
        else:
            weeks = seconds // 604800
            return f"{weeks}w ago"

    @staticmethod
    async def _publish_new_notification(notification: Notification) -> None:
        """
        Publish new notification to Redis for WebSocket delivery.

        Args:
            notification: Notification to publish
        """
        try:
            redis_client = await get_redis()
            if not redis_client:
                return

            message = {
                "event": "notification",
                "data": {
                    "id": str(notification.id),
                    "title": notification.title,
                    "description": notification.description,
                    "type": notification.type,
                    "icon": notification.icon,
                    "action_url": notification.action_url,
                    "metadata": notification.meta_data,
                    "read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                },
            }

            channel = f"notifications:{notification.user_id}"
            await redis_client.publish(channel, json.dumps(message))
            logger.info(f"Published notification to {channel}")

        except Exception as e:
            logger.error(f"Failed to publish notification: {e}")

    @staticmethod
    async def _publish_notification_update(
        user_id: UUID, notification_id: UUID, update_type: str
    ) -> None:
        """
        Publish notification update to Redis.

        Args:
            user_id: User ID
            notification_id: Notification ID
            update_type: Type of update (read, deleted)
        """
        try:
            redis_client = await get_redis()
            if not redis_client:
                return

            if update_type == "read":
                message = {
                    "event": "notification_read",
                    "data": {"notification_id": str(notification_id)},
                }
            elif update_type == "deleted":
                message = {
                    "event": "notification_deleted",
                    "data": {"notification_id": str(notification_id)},
                }
            else:
                return

            channel = f"notifications:{user_id}"
            await redis_client.publish(channel, json.dumps(message))

            # Update badge count
            await NotificationService._publish_badge_update(user_id)

        except Exception as e:
            logger.error(f"Failed to publish notification update: {e}")

    @staticmethod
    async def _publish_all_read_update(user_id: UUID) -> None:
        """
        Publish 'all read' event to Redis.

        Args:
            user_id: User ID
        """
        try:
            redis_client = await get_redis()
            if not redis_client:
                return

            message = {"event": "notifications_cleared", "data": {}}

            channel = f"notifications:{user_id}"
            await redis_client.publish(channel, json.dumps(message))

            # Update badge count
            await NotificationService._publish_badge_update(user_id)

        except Exception as e:
            logger.error(f"Failed to publish all read update: {e}")

    @staticmethod
    async def _publish_badge_update(user_id: UUID) -> None:
        """
        Publish updated badge count to Redis.

        Args:
            user_id: User ID
        """
        try:
            redis_client = await get_redis()
            if not redis_client:
                return

            # Get current unread count from Redis cache or database
            # For now, we'll use a cached value
            cache_key = f"unread_count:{user_id}"
            cached_count = await redis_client.get(cache_key)

            if cached_count is None:
                # If not cached, will be updated by next GET request
                cached_count = 0

            message = {"event": "badge_update", "data": {"count": int(cached_count)}}

            channel = f"notifications:{user_id}"
            await redis_client.publish(channel, json.dumps(message))

        except Exception as e:
            logger.error(f"Failed to publish badge update: {e}")
