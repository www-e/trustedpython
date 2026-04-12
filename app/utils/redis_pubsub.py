"""
Redis pub/sub manager for multi-instance WebSocket synchronization.
Handles message broadcasting across multiple application instances.
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    """
    Manages Redis pub/sub connections for real-time messaging.
    Bridges Redis channels to WebSocket broadcasts.
    """

    def __init__(self) -> None:
        self.pubsub: Any = None
        self._subscribed_channels: set = set()
        self._running = False

    async def publish_to_channel(self, channel: str, message: dict) -> bool:
        """
        Publish message to Redis channel.

        Args:
            channel: Redis channel name (e.g., "chat:room_123")
            message: Message dictionary to publish

        Returns:
            True if published successfully
        """
        try:
            if redis_client is None:
                logger.error("Redis client is not initialized")
                return False

            # Serialize message
            payload = json.dumps(message)

            # Publish to Redis
            result = await redis_client.publish(channel, payload)

            logger.debug(f"Published to {channel}: {result} subscribers")
            return True

        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            return False

    async def subscribe_to_channel(self, channel: str) -> None:
        """
        Subscribe to Redis channel.

        Args:
            channel: Channel name to subscribe
        """
        try:
            if redis_client is None:
                logger.error("Redis client is not initialized")
                return

            if not self.pubsub:
                self.pubsub = redis_client.pubsub()

            await self.pubsub.subscribe(channel)
            self._subscribed_channels.add(channel)
            logger.info(f"Subscribed to channel: {channel}")

        except Exception as e:
            logger.error(f"Error subscribing to {channel}: {e}")

    async def unsubscribe_from_channel(self, channel: str) -> None:
        """
        Unsubscribe from Redis channel.

        Args:
            channel: Channel name to unsubscribe
        """
        try:
            if self.pubsub and channel in self._subscribed_channels:
                await self.pubsub.unsubscribe(channel)
                self._subscribed_channels.discard(channel)
                logger.info(f"Unsubscribed from channel: {channel}")

        except Exception as e:
            logger.error(f"Error unsubscribing from {channel}: {e}")

    async def listen_to_messages(self, message_handler: Callable) -> None:
        """
        Listen for Redis pub/sub messages and pass to handler.

        Args:
            message_handler: Async function to handle received messages
                           Signature: async def handler(channel: str, message: dict)
        """
        if not self.pubsub:
            logger.warning("No pubsub connection to listen on")
            return

        self._running = True
        logger.info("Started listening to Redis pub/sub messages")

        try:
            while self._running:
                try:
                    # Get message with timeout
                    message = await self.pubsub.get_message(timeout=1.0)

                    if message and message["type"] == "message":
                        channel = message["channel"].decode("utf-8")
                        data = message["data"]

                        # Parse JSON payload
                        try:
                            payload = json.loads(data)
                            await message_handler(channel, payload)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in message from {channel}: {e}")

                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")
                    # Continue listening

        except Exception as e:
            logger.error(f"Pub/sub listener error: {e}")

        finally:
            self._running = False
            logger.info("Stopped listening to Redis pub/sub messages")

    def stop_listening(self) -> None:
        """Stop listening to pub/sub messages."""
        self._running = False

    async def close(self) -> None:
        """Close pub/sub connection and cleanup."""
        self.stop_listening()

        if self.pubsub:
            await self.pubsub.close()
            self.pubsub = None

        self._subscribed_channels.clear()
        logger.info("Redis pub/sub connection closed")


# Global pub/sub manager instance
pubsub_manager = RedisPubSubManager()


async def publish_to_channel(channel: str, message: dict) -> bool:
    """
    Convenience function to publish to Redis channel.

    Args:
        channel: Channel name
        message: Message dictionary

    Returns:
        True if published successfully
    """
    return await pubsub_manager.publish_to_channel(channel, message)


async def subscribe_to_channels(patterns: list[str]) -> None:
    """
    Subscribe to multiple Redis channels.

    Args:
        patterns: List of channel patterns (supports wildcards)
                 e.g., ["chat:*", "notifications:user_*"]
    """
    for pattern in patterns:
        try:
            if redis_client is None:
                logger.error("Redis client is not initialized")
                return

            if not pubsub_manager.pubsub:
                pubsub_manager.pubsub = redis_client.pubsub()

            # Use psubscribe for pattern matching
            await pubsub_manager.pubsub.psubscribe(pattern)
            pubsub_manager._subscribed_channels.add(pattern)
            logger.info(f"Subscribed to pattern: {pattern}")

        except Exception as e:
            logger.error(f"Error subscribing to pattern {pattern}: {e}")


async def handle_redis_message(channel: str, message: dict) -> None:
    """
    Handle incoming Redis pub/sub message and broadcast to WebSocket clients.

    Args:
        channel: Redis channel name
        message: Message payload from Redis
    """
    try:
        event = message.get("event")
        data = message.get("data", {})

        if not event:
            return

        # Route based on channel pattern
        if channel.startswith("chat:"):
            await handle_chat_message(channel, event, data)

        elif channel.startswith("notifications:"):
            await handle_notification_message(channel, event, data)

    except Exception as e:
        logger.error(f"Error handling Redis message from {channel}: {e}")


async def handle_chat_message(channel: str, event: str, data: dict) -> None:
    """
    Handle Redis message for chat room.

    Args:
        channel: Channel name (format: "chat:{room_id}")
        event: Event type
        data: Event data
    """
    from app.api.v1.chat.websocket import manager

    # Extract room ID from channel
    try:
        room_id = channel.split(":", 1)[1]
    except IndexError:
        logger.error(f"Invalid channel format: {channel}")
        return

    # Broadcast to all WebSocket connections in room
    if event == "message":
        await manager.broadcast_to_room({"event": "message", "data": data}, room_id)

    elif event == "typing":
        await manager.broadcast_to_room({"event": "typing", "data": data}, room_id)

    elif event == "message_read":
        await manager.broadcast_to_room({"event": "message_read", "data": data}, room_id)

    elif event == "user_joined":
        await manager.broadcast_to_room({"event": "user_joined", "data": data}, room_id)

    elif event == "user_left":
        await manager.broadcast_to_room({"event": "user_left", "data": data}, room_id)


async def handle_notification_message(channel: str, event: str, data: dict) -> None:
    """
    Handle Redis message for user notifications.

    Args:
        channel: Channel name (format: "notifications:{user_id}")
        event: Event type
        data: Event data
    """
    from app.api.v1.chat.websocket import manager

    # Extract user ID from channel
    try:
        user_id = channel.split(":", 1)[1]
    except IndexError:
        logger.error(f"Invalid channel format: {channel}")
        return

    # Send to user's WebSocket connections
    if event == "notification":
        await manager.broadcast_to_user({"event": "notification", "data": data}, user_id)

    elif event == "badge_update":
        await manager.broadcast_to_user({"event": "badge_update", "data": data}, user_id)


async def start_redis_listener() -> None:
    """
    Start Redis pub/sub listener as background task.
    Should be called on application startup.
    """
    from app.core.redis import redis_client
    
    if redis_client is None:
        print("[WARNING] Skipping Redis listener - Redis not available")
        return
    
    # Subscribe to chat room patterns
    await subscribe_to_channels(["chat:*", "notifications:*"])

    # Start listening
    import asyncio

    asyncio.create_task(pubsub_manager.listen_to_messages(handle_redis_message))
    logger.info("Redis pub/sub listener started")


async def stop_redis_listener() -> None:
    """
    Stop Redis pub/sub listener.
    Should be called on application shutdown.
    """
    await pubsub_manager.close()
    logger.info("Redis pub/sub listener stopped")
