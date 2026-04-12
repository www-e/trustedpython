"""
WebSocket connection manager for real-time chat.
Handles room-based connections, broadcasting, and message routing.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for chat rooms.
    Supports room-based messaging and user tracking.
    """

    def __init__(self) -> None:
        # room_id -> {connection_ids: set}
        self.active_rooms: Dict[str, Set[str]] = {}
        # connection_id -> {websocket, user_id, room_id}
        self.active_connections: Dict[str, dict] = {}
        # user_id -> {connection_ids}
        self.user_connections: Dict[str, Set[str]] = {}
        self._connection_counter = 0

    def _generate_connection_id(self) -> str:
        """Generate unique connection identifier."""
        self._connection_counter += 1
        return f"conn_{datetime.utcnow().timestamp()}_{self._connection_counter}"

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str) -> str:
        """
        Accept and track a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: User identifier
            room_id: Room identifier

        Returns:
            Connection ID for tracking
        """
        await websocket.accept()

        connection_id = self._generate_connection_id()

        # Track connection
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "room_id": room_id,
            "connected_at": datetime.utcnow(),
        }

        # Add to room
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = set()
        self.active_rooms[room_id].add(connection_id)

        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        logger.info(f"Connection {connection_id} established: user={user_id}, room={room_id}")

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Remove connection and clean up tracking.

        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id not in self.active_connections:
            return

        conn_data = self.active_connections[connection_id]
        user_id = conn_data["user_id"]
        room_id = conn_data["room_id"]

        # Remove from room
        if room_id in self.active_rooms:
            self.active_rooms[room_id].discard(connection_id)
            # Clean up empty rooms
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove connection
        del self.active_connections[connection_id]

        logger.info(f"Connection {connection_id} closed: user={user_id}, room={room_id}")

    async def send_personal_message(self, message: dict, connection_id: str) -> None:
        """
        Send message to specific connection.

        Args:
            message: Message dictionary to send
            connection_id: Target connection identifier
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        websocket = self.active_connections[connection_id]["websocket"]
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def broadcast_to_room(
        self, message: dict, room_id: str, exclude_connection_id: Optional[str] = None
    ) -> None:
        """
        Broadcast message to all connections in a room.

        Args:
            message: Message dictionary to broadcast
            room_id: Target room identifier
            exclude_connection_id: Optional connection to exclude
        """
        if room_id not in self.active_rooms:
            logger.debug(f"Room {room_id} has no active connections")
            return

        disconnected = set()

        for connection_id in self.active_rooms[room_id]:
            if exclude_connection_id and connection_id == exclude_connection_id:
                continue

            if connection_id not in self.active_connections:
                disconnected.add(connection_id)
                continue

            websocket = self.active_connections[connection_id]["websocket"]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.add(connection_id)

        # Clean up disconnected connections
        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def broadcast_to_user(self, message: dict, user_id: str) -> None:
        """
        Send message to all active connections for a user.

        Args:
            message: Message dictionary to send
            user_id: Target user identifier
        """
        if user_id not in self.user_connections:
            logger.debug(f"User {user_id} has no active connections")
            return

        for connection_id in self.user_connections[user_id]:
            await self.send_personal_message(message, connection_id)

    def get_room_connections(self, room_id: str) -> List[dict]:
        """
        Get all connection data for a room.

        Args:
            room_id: Room identifier

        Returns:
            List of connection dictionaries
        """
        if room_id not in self.active_rooms:
            return []

        connections = []
        for conn_id in self.active_rooms[room_id]:
            if conn_id in self.active_connections:
                conn_data = self.active_connections[conn_id].copy()
                conn_data["connection_id"] = conn_id
                # Remove websocket from return data
                conn_data.pop("websocket", None)
                connections.append(conn_data)

        return connections

    def get_active_users_in_room(self, room_id: str) -> Set[str]:
        """
        Get unique active users in a room.

        Args:
            room_id: Room identifier

        Returns:
            Set of user IDs
        """
        connections = self.get_room_connections(room_id)
        return {conn["user_id"] for conn in connections}

    def is_user_in_room(self, user_id: str, room_id: str) -> bool:
        """
        Check if user has active connection in room.

        Args:
            user_id: User identifier
            room_id: Room identifier

        Returns:
            True if user is active in room
        """
        active_users = self.get_active_users_in_room(room_id)
        return user_id in active_users


# Global connection manager instance
manager = ConnectionManager()
