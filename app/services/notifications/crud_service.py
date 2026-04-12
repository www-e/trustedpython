"""
Notification CRUD operations service.

This module handles all create, read, update, and delete operations
for notifications, including querying, filtering, and pagination.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    CreateNotificationRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationType,
)
from app.services.notifications.base import (
    get_relative_time,
    publish_badge_update,
    publish_new_notification,
    publish_notification_update,
)

logger = logging.getLogger(__name__)


class NotificationCrudService:
    """
    Service for notification CRUD operations.

    Provides methods for creating, retrieving, updating, and deleting
    notifications with full support for filtering, pagination, and
    real-time updates via WebSocket.
    """

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
        from app.services.notifications.preferences_service import NotificationPreferencesService

        unread_count = await NotificationPreferencesService.get_unread_count(db, user_id)

        # Convert to response format
        notification_responses = []
        for notification in notifications:
            notification_responses.append(
                NotificationCrudService._notification_to_response(notification)
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

        return NotificationCrudService._notification_to_response(notification)

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
            await publish_notification_update(user_id, notification_id, "read")

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
        from app.services.notifications.base import publish_all_read_update

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
        await publish_all_read_update(user_id)

        return {"success": True, "data": {"marked_count": marked_count}}

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
        await publish_notification_update(user_id, notification_id, "deleted")

        return {"success": True, "message": "Notification deleted"}

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
            icon = NotificationCrudService.ICONS.get(notification_type, "notifications")

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
        await publish_new_notification(notification)

        # Publish badge count update
        await publish_badge_update(user_id)

        return NotificationCrudService._notification_to_response(notification)

    @staticmethod
    def _notification_to_response(notification: Notification) -> NotificationResponse:
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
            relative_time=get_relative_time(notification.created_at),
        )
