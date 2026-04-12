"""
WebSocket endpoint for real-time notifications.
Pushes notifications directly to user's connected clients.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.api.v1.chat.websocket import manager
from app.core.security import decode_token
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_notification_user(token: str) -> User:
    """
    Authenticate notification WebSocket connection.

    Args:
        token: JWT access token

    Returns:
        Authenticated user

    Raises:
        WebSocketDisconnect: If authentication fails
    """
    try:
        payload = decode_token(token)
        if payload is None:
            raise ValueError("Invalid token payload")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        return User(id=user_id, email=f"{user_id}@example.com")
    except Exception as e:
        logger.error(f"Notification WebSocket authentication failed: {e}")
        raise WebSocketDisconnect(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed"
        )


@router.get("/ws")
async def notifications_websocket(
    websocket: WebSocket, token: str = Query(..., description="JWT access token")
) -> None:
    """
    WebSocket endpoint for real-time notifications.

    Query Parameters:
        token: JWT access token for authentication

    Events Sent (Server -> Client):
        - notification: New notification
          {
            "event": "notification",
            "data": {
              "id": "...",
              "type": "message|system|alert",
              "title": "...",
              "body": "...",
              "data": {...},
              "read": false,
              "created_at": "..."
            }
          }
        - badge_update: Unread count updated
          {"event": "badge_update", "data": {"count": 5}}
        - notification_read: Notification marked as read
          {"event": "notification_read", "data": {"notification_id": "..."}}
        - notifications_cleared: All notifications cleared
          {"event": "notifications_cleared", "data": {}}
        - error: Error occurred
          {"event": "error", "data": {"message": "..."}}

    Events Accepted (Client -> Server):
        - mark_read: Mark notification as read
          {"event": "mark_read", "notification_id": "..."}
        - clear_all: Clear all notifications
          {"event": "clear_all"}
    """
    # Authenticate user
    user = await get_notification_user(token)
    user_id = str(user.id)

    # Accept connection
    await websocket.accept()

    # Create special connection ID for notifications
    # Use room_id as "notifications" to separate from chat connections
    connection_id = await manager.connect(websocket, user_id, room_id=f"notifications_{user_id}")

    logger.info(f"Notification WebSocket connected: {connection_id}")

    # Send initial unread count
    # In production, fetch from database
    initial_count = await get_unread_notification_count(user_id)
    await websocket.send_json({"event": "badge_update", "data": {"count": initial_count}})

    try:
        while True:
            # Receive JSON from client
            data = await websocket.receive_json()
            if not data:
                continue
            event = data.get("event")

            if not event:
                await websocket.send_json(
                    {"event": "error", "data": {"message": "Missing event type"}}
                )
                continue

            # Handle client events
            if event == "mark_read":
                await handle_mark_read(user_id, data.get("notification_id"))

            elif event == "clear_all":
                await handle_clear_all(user_id)

            else:
                await websocket.send_json(
                    {"event": "error", "data": {"message": f"Unknown event type: {event}"}}
                )

    except WebSocketDisconnect:
        logger.info(f"Notification WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"Notification WebSocket error for {connection_id}: {e}")
        await websocket.send_json({"event": "error", "data": {"message": "Internal server error"}})

    finally:
        # Clean up connection
        await manager.disconnect(connection_id)


async def handle_mark_read(user_id: str, notification_id: Optional[str]) -> None:
    """
    Handle marking notification as read.

    Args:
        user_id: User ID
        notification_id: Notification ID to mark as read
    """
    if not notification_id:
        return

    # In production, update database
    # await mark_notification_read(user_id, notification_id)

    # Update unread count
    new_count = await get_unread_notification_count(user_id)

    # Send confirmation and updated count to all user's connections
    await manager.broadcast_to_user(
        {"event": "notification_read", "data": {"notification_id": notification_id}}, user_id
    )

    await manager.broadcast_to_user(
        {"event": "badge_update", "data": {"count": new_count}}, user_id
    )


async def handle_clear_all(user_id: str) -> None:
    """
    Handle clearing all notifications.

    Args:
        user_id: User ID
    """
    # In production, update database
    # await clear_all_notifications(user_id)

    # Send confirmation and updated count
    await manager.broadcast_to_user({"event": "notifications_cleared", "data": {}}, user_id)

    await manager.broadcast_to_user({"event": "badge_update", "data": {"count": 0}}, user_id)


async def get_unread_notification_count(user_id: str) -> int:
    """
    Get unread notification count for user.

    Args:
        user_id: User ID

    Returns:
        Unread count
    """
    # In production, fetch from database
    # return await db.query(Notification).filter_by(user_id=user_id, read=False).count()
    return 0


async def push_notification(user_id: str, notification: dict) -> None:
    """
    Push notification to user's connected clients.

    Args:
        user_id: Target user ID
        notification: Notification data
    """
    message = {
        "event": "notification",
        "data": {
            "id": str(notification.get("id", "")),
            "type": notification.get("type", "system"),
            "title": notification.get("title", ""),
            "body": notification.get("body", ""),
            "data": notification.get("data", {}),
            "read": notification.get("read", False),
            "created_at": notification.get("created_at", datetime.utcnow().isoformat()),
        },
    }

    # Broadcast to user's connections
    await manager.broadcast_to_user(message, user_id)

    # Update badge count
    new_count = await get_unread_notification_count(user_id)
    await manager.broadcast_to_user(
        {"event": "badge_update", "data": {"count": new_count}}, user_id
    )


# Required imports
from datetime import datetime
