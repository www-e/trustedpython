"""
WebSocket routes for real-time chat.
Handles message events, typing indicators, and room management.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.v1.chat.websocket import manager
from app.core.security import decode_token
from app.models.chat import ChatRoom
from app.models.user import User
from app.utils.redis_pubsub import publish_to_channel

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_websocket_user(token: str) -> User:
    """
    Authenticate WebSocket connection with JWT token.

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

        # In production, fetch user from DB
        # For now, return basic user object
        return User(id=user_id, email=f"{user_id}@example.com")
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        raise WebSocketDisconnect(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed"
        )


async def verify_room_access(user_id: str, room_id: str) -> bool:
    """
    Verify user has access to the chat room.

    Args:
        user_id: User identifier
        room_id: Room identifier

    Returns:
        True if user can access room
    """
    # In production, check database for room membership
    # For now, allow access
    return True


@router.get("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    room_id: str = Query(..., description="Chat room ID"),
) -> None:
    """
    WebSocket endpoint for real-time chat.

    Query Parameters:
        token: JWT access token for authentication
        room_id: Chat room identifier to join

    Events Accepted (Client -> Server):
        - message: Send chat message
          {"event": "message", "room_id": "...", "content": "...", "type": "text"}
        - typing: Typing indicator
          {"event": "typing", "room_id": "..."}
        - read: Mark message as read
          {"event": "read", "room_id": "...", "message_id": "..."}
        - join_room: Join additional room
          {"event": "join_room", "room_id": "..."}
        - leave_room: Leave room
          {"event": "leave_room", "room_id": "..."

    Events Sent (Server -> Client):
        - message: New chat message
          {"event": "message", "data": {...}}
        - typing: User typing indicator
          {"event": "typing", "data": {"user_id": "...", "room_id": "..."}}
        - user_joined: User joined room
          {"event": "user_joined", "data": {"user_id": "...", "room_id": "..."}}
        - user_left: User left room
          {"event": "user_left", "data": {"user_id": "...", "room_id": "..."}}
        - error: Error occurred
          {"event": "error", "data": {"message": "..."}}
    """
    # Authenticate user
    user = await get_websocket_user(token)
    user_id = str(user.id)

    # Verify room access
    if not await verify_room_access(user_id, room_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Room access denied")
        return

    # Accept connection and add to manager
    connection_id = await manager.connect(websocket, user_id, room_id)

    # Notify others in room
    await manager.broadcast_to_room(
        {
            "event": "user_joined",
            "data": {
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        },
        room_id,
        exclude_connection_id=connection_id,
    )

    # Publish join event to Redis for other instances
    await publish_to_channel(
        f"chat:{room_id}",
        {
            "event": "user_joined",
            "data": {
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        },
    )

    try:
        while True:
            # Receive JSON message from client
            data = await websocket.receive_json()
            if not data:
                continue
            event = data.get("event")

            if not event:
                await websocket.send_json(
                    {"event": "error", "data": {"message": "Missing event type"}}
                )
                continue

            # Handle different event types
            if event == "message":
                await handle_message_event(user_id, room_id, data, connection_id)

            elif event == "typing":
                await handle_typing_event(user_id, room_id, connection_id)

            elif event == "read":
                await handle_read_event(user_id, room_id, data.get("message_id"))

            elif event == "join_room":
                new_room_id = data.get("room_id")
                if new_room_id and new_room_id != room_id:
                    await handle_join_room(user_id, new_room_id, connection_id)

            elif event == "leave_room":
                await handle_leave_room(user_id, room_id, connection_id)
                # Break loop to disconnect after leaving
                break

            else:
                await websocket.send_json(
                    {"event": "error", "data": {"message": f"Unknown event type: {event}"}}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        await websocket.send_json({"event": "error", "data": {"message": "Internal server error"}})

    finally:
        # Notify others user left
        await manager.broadcast_to_room(
            {
                "event": "user_left",
                "data": {
                    "user_id": user_id,
                    "room_id": room_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            room_id,
        )

        # Publish leave event to Redis
        await publish_to_channel(
            f"chat:{room_id}",
            {"event": "user_left", "data": {"user_id": user_id, "room_id": room_id}},
        )

        # Clean up connection
        await manager.disconnect(connection_id)


async def handle_message_event(user_id: str, room_id: str, data: dict, connection_id: str) -> None:
    """
    Handle incoming message event.

    Args:
        user_id: Sender user ID
        room_id: Target room ID
        data: Event data
        connection_id: Sender's connection ID
    """
    content = data.get("content")
    message_type = data.get("type", "text")

    if not content:
        await manager.send_personal_message(
            {"event": "error", "data": {"message": "Message content is required"}}, connection_id
        )
        return

    # Create message object
    message = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "sender_id": user_id,
        "content": content,
        "type": message_type,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # In production, save to database here
    # await save_message_to_db(message)

    # Broadcast to room (including sender for confirmation)
    await manager.broadcast_to_room({"event": "message", "data": message}, room_id)

    # Publish to Redis for other instances
    await publish_to_channel(f"chat:{room_id}", {"event": "message", "data": message})


async def handle_typing_event(user_id: str, room_id: str, connection_id: str) -> None:
    """
    Handle typing indicator event.

    Args:
        user_id: Typing user ID
        room_id: Target room ID
        connection_id: Sender's connection ID
    """
    typing_message = {
        "event": "typing",
        "data": {
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    # Broadcast to room (excluding sender)
    await manager.broadcast_to_room(typing_message, room_id, exclude_connection_id=connection_id)

    # Publish to Redis
    await publish_to_channel(f"chat:{room_id}", typing_message)


async def handle_read_event(user_id: str, room_id: str, message_id: Optional[str]) -> None:
    """
    Handle message read receipt.

    Args:
        user_id: User who read the message
        room_id: Room ID
        message_id: Message that was read
    """
    if not message_id:
        return

    # In production, update read receipts in database
    # await mark_message_as_read(user_id, message_id)

    # Notify room members
    read_message = {
        "event": "message_read",
        "data": {
            "message_id": message_id,
            "room_id": room_id,
            "read_by": user_id,
            "read_at": datetime.utcnow().isoformat(),
        },
    }

    await manager.broadcast_to_room(read_message, room_id)
    await publish_to_channel(f"chat:{room_id}", read_message)


async def handle_join_room(user_id: str, new_room_id: str, connection_id: str) -> None:
    """
    Handle user joining additional room.

    Args:
        user_id: User ID
        new_room_id: Room to join
        connection_id: Connection ID
    """
    # Verify access
    if not await verify_room_access(user_id, new_room_id):
        await manager.send_personal_message(
            {"event": "error", "data": {"message": "Room access denied"}}, connection_id
        )
        return

    # Add connection to new room
    current_conn = manager.active_connections.get(connection_id)
    if current_conn:
        # Add to new room
        if new_room_id not in manager.active_rooms:
            manager.active_rooms[new_room_id] = set()
        manager.active_rooms[new_room_id].add(connection_id)

        # Notify new room
        await manager.broadcast_to_room(
            {
                "event": "user_joined",
                "data": {
                    "user_id": user_id,
                    "room_id": new_room_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            new_room_id,
            exclude_connection_id=connection_id,
        )

        # Publish to Redis
        await publish_to_channel(
            f"chat:{new_room_id}",
            {"event": "user_joined", "data": {"user_id": user_id, "room_id": new_room_id}},
        )


async def handle_leave_room(user_id: str, room_id: str, connection_id: str) -> None:
    """
    Handle user leaving room.

    Args:
        user_id: User ID
        room_id: Room to leave
        connection_id: Connection ID
    """
    # Remove from room
    if room_id in manager.active_rooms:
        manager.active_rooms[room_id].discard(connection_id)

    # Notify remaining users
    await manager.broadcast_to_room(
        {
            "event": "user_left",
            "data": {
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        },
        room_id,
    )

    # Publish to Redis
    await publish_to_channel(
        f"chat:{room_id}", {"event": "user_left", "data": {"user_id": user_id, "room_id": room_id}}
    )
