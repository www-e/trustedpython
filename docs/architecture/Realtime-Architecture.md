# Real-Time Architecture

## ⚡ Real-Time Overview

**Technology Stack:**
- **FastAPI WebSockets** - Native WebSocket support
- **Redis Pub/Sub** - Horizontal scaling, message broadcasting
- **Asyncio** - Asynchronous connection management

**Use Cases:**
- 3-way deal chat rooms (Group, Buyer-Mediator private, Seller-Mediator private)
- Real-time typing indicators
- Online/offline status
- Deal status updates
- Push notification triggers

---

## 🏗️ WebSocket Architecture

### Connection Flow

```
┌─────────────┐                    ┌─────────────┐
│   Flutter   │                    │  FastAPI    │
│    App      │                    │   Server    │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. WebSocket Connect            │
       │  wss://api/ws/chat/{chat_id}     │
       │  ?token={JWT}                    │
       ├─────────────────────────────────>│
       │                                  │
       │                        2. Validate JWT
       │                        3. Load Chat
       │                        4. Add to connection pool
       │                                  │
       │  5. Connection Established       │
       │<─────────────────────────────────┤
       │                                  │
       │  6. Send Message                 │
       │  { "content": "Hello" }          │
       ├─────────────────────────────────>│
       │                                  │
       │                        7. Publish to Redis
       │                        8. Save to PostgreSQL
       │                                  │
       │          9. Broadcast to all     │
       │          servers via Redis       │
       │<─────────────────────────────────┤
       │                                  │
┌──────┴──────┐                    ┌──────┴──────┐
│   Flutter   │                    │  FastAPI    │
│    App      │                    │   Server 2  │
└─────────────┘                    └─────────────┘
                                            │
                                    10. Receive from Redis
                                    11. Forward to clients
```

---

## 🔌 WebSocket Authentication

### Connection URL

```
wss://api.marketplace.com/ws/chat/{chat_id}?token={JWT}
```

### Authentication Flow

```python
# websocket/auth.py

async def validate_websocket_token(
    websocket: WebSocket,
    token: str,
    chat_id: int
) -> User:
    """Validate JWT and user access to chat"""

    # 1. Validate JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        raise WebSocketException(code=1008, reason="Invalid token")

    # 2. Load user
    user = await user_service.get(user_id)
    if not user:
        await websocket.close(code=1008, reason="User not found")
        raise WebSocketException(code=1008, reason="User not found")

    # 3. Verify chat access
    chat = await chat_service.get(chat_id)
    if not chat:
        await websocket.close(code=1008, reason="Chat not found")
        raise WebSocketException(code=1008, reason="Chat not found")

    # 4. Check if user is participant
    is_participant = await chat_service.is_participant(chat_id, user_id)
    if not is_participant:
        await websocket.close(code=1003, reason="Access denied")
        raise WebSocketException(code=1003, reason="Access denied")

    # 5. Check if chat is read-only
    if chat.is_read_only:
        await websocket.close(code=1003, reason="Chat is read-only")
        raise WebSocketException(code=1003, reason="Chat is read-only")

    return user
```

### WebSocket Endpoint

```python
# websocket/chat.py

@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle WebSocket chat connection"""

    # Accept connection
    await websocket.accept()

    # Authenticate
    try:
        user = await validate_websocket_token(websocket, token, chat_id)
    except WebSocketException:
        return  # Connection already closed

    # Add to connection manager
    await manager.connect(websocket, chat_id, user.id)

    try:
        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_content = data.get("content")
            message_type = data.get("type", "text")

            # Validate message
            if not message_content:
                await websocket.send_json({
                    "error": "Message content is required"
                })
                continue

            # Create message
            message = await chat_service.create_message(
                chat_id=chat_id,
                sender_id=user.id,
                content=message_content,
                message_type=message_type
            )

            # Broadcast to all participants
            await manager.broadcast_to_chat(
                chat_id=chat_id,
                message=message_to_dict(message),
                exclude_user_id=user.id
            )

            # Send push notification to offline users
            await notify_offline_participants(chat_id, message)

    except WebSocketDisconnect:
        # Remove from connection manager
        await manager.disconnect(chat_id, user.id)

        # Broadcast user left
        await manager.broadcast_to_chat(
            chat_id=chat_id,
            message={
                "type": "system",
                "content": f"{user.username} left the chat"
            }
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
```

---

## 📡 Redis Pub/Sub

### Why Redis Pub/Sub?

**Single Server Limitation:**
```
Server 1 (WebSocket connections A, B, C)
  ↓
  Message from A
  ↓
  Only A, B, C receive it
  ✗ D, E, F on Server 2 don't receive it
```

**Redis Pub/Sub Solution:**
```
Server 1 (A, B, C) ──┐
                     ├──→ Redis Pub/Sub ←──┐
Server 2 (D, E, F) ──┘                     │
                                          │
                                     Broadcast to all
                                          │
Server 1 ←─────────────────────────────────┘
Server 2 ←─────────────────────────────────┘
```

### Redis Implementation

```python
# websocket/manager.py

class ConnectionManager:
    """Manage WebSocket connections with Redis pub/sub"""

    def __init__(self):
        # Local connection storage (server-specific)
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # chat_id -> {user_id -> WebSocket}

        # Redis pub/sub
        self.redis_pub = redis.asyncio.from_url(REDIS_URL)
        self.redis_sub = redis.asyncio.from_url(REDIS_URL)
        self.pubsub = self.redis_sub.pubsub()

        # Start listener
        asyncio.create_task(self.listen_to_redis())

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Add connection to local pool"""
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}

        self.active_connections[chat_id][user_id] = websocket

        # Subscribe to Redis channel
        await self.pubsub.subscribe(f"chat:{chat_id}")

    async def disconnect(self, chat_id: int, user_id: int):
        """Remove connection from local pool"""
        if chat_id in self.active_connections:
            self.active_connections[chat_id].pop(user_id, None)

            # Unsubscribe if no more connections
            if not self.active_connections[chat_id]:
                await self.pubsub.unsubscribe(f"chat:{chat_id}")
                del self.active_connections[chat_id]

    async def broadcast_to_chat(
        self,
        chat_id: int,
        message: dict,
        exclude_user_id: int = None
    ):
        """Broadcast message to local connections + Redis"""
        # 1. Send to local connections
        if chat_id in self.active_connections:
            for user_id, websocket in self.active_connections[chat_id].items():
                if exclude_user_id and user_id == exclude_user_id:
                    continue
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")

        # 2. Publish to Redis for other servers
        await self.redis_pub.publish(
            f"chat:{chat_id}",
            json.dumps({
                "message": message,
                "exclude_user_id": exclude_user_id
            })
        )

    async def listen_to_redis(self):
        """Listen for Redis messages and forward to local clients"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                chat_id = int(message['channel'].split(':')[1])

                # Forward to local connections
                if chat_id in self.active_connections:
                    msg = data['message']
                    exclude = data.get('exclude_user_id')

                    for user_id, websocket in self.active_connections[chat_id].items():
                        if exclude and user_id == exclude:
                            continue
                        try:
                            await websocket.send_json(msg)
                        except Exception as e:
                            logger.error(f"Failed to forward Redis message: {e}")
```

---

## 💬 Chat System Design

### Chat Room Types

#### 1. Group Chat (Buyer + Seller + Mediator)
```
┌─────────────────────────────────────┐
│       Deal #123 - Group Chat        │
├─────────────────────────────────────┤
│ Buyer: I'm interested in buying     │
│ Seller: Great! Price is $50         │
│ Mediator: Let me know when ready    │
│ Buyer: Just sent payment proof      │
│ Mediator: Verifying...              │
└─────────────────────────────────────┘
```

#### 2. Buyer-Mediator Private Chat
```
┌─────────────────────────────────────┐
│     Private: Buyer ↔ Mediator       │
├─────────────────────────────────────┤
│ Buyer: [Uploads payment screenshot] │
│ Mediator: Payment confirmed ✓       │
│ Mediator: Requesting credentials    │
└─────────────────────────────────────┘
```

#### 3. Seller-Mediator Private Chat
```
┌─────────────────────────────────────┐
│    Private: Seller ↔ Mediator       │
├─────────────────────────────────────┤
│ Mediator: Payment received          │
│ Seller: Here are credentials        │
│ Seller: [Uploads account info]      │
│ Mediator: Credentials verified ✓    │
└─────────────────────────────────────┘
```

### Chat Creation Flow

```python
# services/chat_service.py

async def create_deal_chats(deal: Deal) -> List[Chat]:
    """Create 3 chat rooms for a deal"""

    chats = []

    # 1. Group chat
    group_chat = await self.create_chat(
        deal_id=deal.id,
        chat_type=ChatType.GROUP,
        name=f"Deal #{deal.id} - Group Chat"
    )
    await self.add_participants(group_chat.id, [
        deal.buyer_id,
        deal.seller_id,
        deal.mediator_id
    ])
    chats.append(group_chat)

    # 2. Buyer-Mediator private chat
    buyer_chat = await self.create_chat(
        deal_id=deal.id,
        chat_type=ChatType.BUYER_MEDIATOR_PRIVATE,
        name=f"Deal #{deal.id} - Private (Buyer)"
    )
    await self.add_participants(buyer_chat.id, [
        deal.buyer_id,
        deal.mediator_id
    ])
    chats.append(buyer_chat)

    # 3. Seller-Mediator private chat
    seller_chat = await self.create_chat(
        deal_id=deal.id,
        chat_type=ChatType.SELLER_MEDIATOR_PRIVATE,
        name=f"Deal #{deal.id} - Private (Seller)"
    )
    await self.add_participants(seller_chat.id, [
        deal.seller_id,
        deal.mediator_id
    ])
    chats.append(seller_chat)

    # Send system messages
    for chat in chats:
        await self.create_system_message(
            chat_id=chat.id,
            content="Chat created. Deal initiated."
        )

    return chats
```

---

## 🔔 Real-Time Notifications

### Push Notification Flow

```
1. User sends message in chat
   ↓
2. Message saved to database
   ↓
3. WebSocket broadcast to online users
   ↓
4. Celery task: Check offline participants
   ↓
5. If offline → Send OneSignal push
   ↓
6. OneSignal delivers to mobile devices
```

### Implementation

```python
# tasks/notifications.py

@celery_app.task
async def notify_new_message(
    chat_id: int,
    message_id: int,
    sender_id: int
):
    """Send push notification for new message"""

    # Get chat participants
    participants = await chat_service.get_participants(chat_id)

    # Filter out sender
    recipients = [p for p in participants if p.user_id != sender_id]

    # Check who's offline
    offline_recipients = [
        p for p in recipients
        if not await is_user_online(p.user_id)
    ]

    if not offline_recipients:
        return  # Everyone online, no push needed

    # Get message details
    message = await chat_service.get_message(message_id)
    sender = await user_service.get(sender_id)

    # Send push notifications
    for recipient in offline_recipients:
        await onesignal_client.send_notification(
            player_id=recipient.player_id,
            heading=f"New message from {sender.username}",
            content=message.content,
            data={
                "type": "new_message",
                "chat_id": chat_id,
                "message_id": message_id
            }
        )
```

---

## 📊 Online/Offline Status

### Tracking Active Connections

```python
# websocket/manager.py

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # Also track user presence
        self.user_presence: Dict[int, datetime] = {}

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        # ... connection logic ...

        # Update user presence
        self.user_presence[user_id] = datetime.now()

        # Broadcast user online to all their chats
        await self.broadcast_user_status(user_id, "online")

    async def disconnect(self, chat_id: int, user_id: int):
        # ... disconnection logic ...

        # Remove from presence if no more connections
        user_connections = self.count_user_connections(user_id)
        if user_connections == 0:
            self.user_presence.pop(user_id, None)
            await self.broadcast_user_status(user_id, "offline")

    async def broadcast_user_status(self, user_id: int, status: str):
        """Broadcast user status to all chats they're in"""
        user_chats = await chat_service.get_user_chats(user_id)

        for chat in user_chats:
            await self.broadcast_to_chat(
                chat_id=chat.id,
                message={
                    "type": "presence",
                    "user_id": user_id,
                    "status": status
                }
            )
```

### Heartbeat Mechanism

```python
# Client side (Flutter)
// Send ping every 30 seconds
Timer.periodic(Duration(seconds: 30), (timer) async {
  websocketChannel.sink.add(jsonEncode({
    "type": "ping",
    "timestamp": DateTime.now().toIso8601String()
  }));
});

// Server side
@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket_endpoint(websocket: WebSocket, ...):
    last_ping = datetime.now()

    while True:
        data = await websocket.receive_json()

        if data.get("type") == "ping":
            last_ping = datetime.now()
            await websocket.send_json({"type": "pong"})

        # Check timeout (no ping for 60 seconds)
        if datetime.now() - last_ping > timedelta(seconds=60):
            await websocket.close()
            break
```

---

## 🔒 Security & Validation

### Message Validation

```python
# services/chat_service.py

async def create_message(
    self,
    chat_id: int,
    sender_id: int,
    content: str,
    message_type: MessageType = MessageType.TEXT
) -> Message:
    """Create and validate chat message"""

    # 1. Validate chat access
    chat = await self.chat_repo.get(chat_id)
    if not chat:
        raise NotFoundError("Chat not found")

    is_participant = await self.is_participant(chat_id, sender_id)
    if not is_participant:
        raise ForbiddenError("Not a chat participant")

    # 2. Validate chat is not read-only
    if chat.is_read_only:
        raise ForbiddenError("Chat is read-only")

    # 3. Validate content
    if not content or len(content.strip()) == 0:
        raise ValidationError("Message cannot be empty")

    if len(content) > MAX_MESSAGE_LENGTH:
        raise ValidationError("Message too long")

    # 4. Rate limiting (check via Redis)
    rate_limit_key = f"chat_rate:{sender_id}:{chat_id}"
    message_count = await redis.incr(rate_limit_key)
    if message_count == 1:
        await redis.expire(rate_limit_key, 60)  # 1 minute window

    if message_count > MAX_MESSAGES_PER_MINUTE:
        raise RateLimitError("Too many messages")

    # 5. Create message
    message = await self.message_repo.create(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content.strip(),
        message_type=message_type
    )

    # 6. Update unread counts for other participants
    await self.update_unread_counts(chat_id, sender_id)

    return message
```

---

## 🧪 Testing WebSocket Connections

### Pytest WebSocket Tests

```python
# tests/integration/websocket/test_chat.py

@pytest.mark.asyncio
async def test_chat_websocket_connection(auth_token, test_client):
    """Test WebSocket connection and messaging"""

    # 1. Connect to WebSocket
    async with test_client.websocket_connect(
        f"/ws/chat/1?token={auth_token}"
    ) as websocket:
        # 2. Send message
        await websocket.send_json({
            "content": "Hello, world!"
        })

        # 3. Receive response
        data = await websocket.receive_json()
        assert data["content"] == "Hello, world!"
        assert "sender_id" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_chat_authentication_failure(test_client):
    """Test WebSocket connection with invalid token"""

    with pytest.raises(WebSocketDisconnect) as exc:
        async with test_client.websocket_connect(
            "/ws/chat/1?token=invalid_token"
        ):
            pass

    assert exc.value.code == 1008  # Policy violation
```

---

## 📚 Related Documentation

- [Architecture Design](../02-Architecture-Design.md) - Overall system architecture
- [API Structure](./API-Structure.md) - REST API endpoints
- [Database Schema](../database/Database-Schema.md) - Chat data models

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
