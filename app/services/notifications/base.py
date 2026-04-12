"""
Base utilities and shared functionality for notification services.

This module provides common helper functions used across notification service modules,
including formatting utilities, Redis publishing, and response conversions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

if TYPE_CHECKING:
    from app.models.notification import Notification

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


def get_relative_time(created_at: datetime) -> str:
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


async def publish_new_notification(notification: "Notification") -> None:
    """
    Publish new notification to Redis for WebSocket delivery.

    Args:
        notification: Notification model to publish
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


async def publish_notification_update(
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
        await publish_badge_update(user_id)

    except Exception as e:
        logger.error(f"Failed to publish notification update: {e}")


async def publish_all_read_update(user_id: UUID) -> None:
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
        await publish_badge_update(user_id)

    except Exception as e:
        logger.error(f"Failed to publish all read update: {e}")


async def publish_badge_update(user_id: UUID) -> None:
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


async def send_push_notification(user_id: UUID, notification: "Notification") -> None:
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
