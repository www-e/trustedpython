# WebSocket Infrastructure Documentation

## Overview

Real-time communication system using WebSockets with Redis pub/sub for multi-instance synchronization. Supports chat rooms, typing indicators, and push notifications.

## Architecture

```
Client (Browser)
    ↓ WebSocket
FastAPI Instance 1
    ↓ Redis Pub/Sub
FastAPI Instance 2
    ↓ Redis Pub/Sub
FastAPI Instance N
    ↓
Redis Server
```

## Components

### 1. Connection Manager (`app/api/v1/chat/websocket.py`)

**Purpose:** Track and manage WebSocket connections

**Key Features:**
- Room-based connection grouping
- User connection tracking
- Automatic cleanup on disconnect
- Room broadcasting with exclusion
- Personal messaging

**Methods:**
```python
await manager.connect(websocket, user_id, room_id)  # Returns connection_id
await manager.disconnect(connection_id)
await manager.send_personal_message(message, connection_id)
await manager.broadcast_to_room(message, room_id, exclude_connection_id)
await manager.broadcast_to_user(message, user_id)
manager.get_room_connections(room_id)
manager.get_active_users_in_room(room_id)
manager.is_user_in_room(user_id, room_id)
```

### 2. Chat WebSocket Routes (`app/api/v1/chat/routes.py`)

**Endpoint:** `GET /api/v1/chat/ws?token={jwt}&room_id={room_id}`

**Event Flow:**

#### Client → Server Events

**Message Event:**
```json
{
  "event": "message",
  "room_id": "room_123",
  "content": "Hello, world!",
  "type": "text"
}
```

**Typing Event:**
```json
{
  "event": "typing",
  "room_id": "room_123"
}
```

**Read Receipt:**
```json
{
  "event": "read",
  "room_id": "room_123",
  "message_id": "msg_456"
}
```

**Join Room:**
```json
{
  "event": "join_room",
  "room_id": "room_789"
}
```

**Leave Room:**
```json
{
  "event": "leave_room",
  "room_id": "room_123"
}
```

#### Server → Client Events

**Message Broadcast:**
```json
{
  "event": "message",
  "data": {
    "id": "msg_456",
    "room_id": "room_123",
    "sender_id": "user_789",
    "content": "Hello, world!",
    "type": "text",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Typing Indicator:**
```json
{
  "event": "typing",
  "data": {
    "user_id": "user_789",
    "room_id": "room_123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**User Joined:**
```json
{
  "event": "user_joined",
  "data": {
    "user_id": "user_789",
    "room_id": "room_123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**User Left:**
```json
{
  "event": "user_left",
  "data": {
    "user_id": "user_789",
    "room_id": "room_123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Error:**
```json
{
  "event": "error",
  "data": {
    "message": "Error description"
  }
}
```

### 3. Redis Pub/Sub Manager (`app/utils/redis_pubsub.py`)

**Purpose:** Synchronize messages across multiple FastAPI instances

**Channels:**
- `chat:{room_id}` - Chat room messages
- `notifications:{user_id}` - User notifications

**Key Functions:**
```python
# Publish to Redis channel
await publish_to_channel(f"chat:{room_id}", message_dict)

# Subscribe to channel patterns
await subscribe_to_channels(["chat:*", "notifications:*"])

# Start listener (called in lifespan)
await start_redis_listener()

# Stop listener (called in lifespan)
await stop_redis_listener()
```

**Message Flow:**
1. User sends message via WebSocket
2. Handler processes and saves to database
3. Handler publishes to Redis channel
4. All instances receive via pub/sub
5. Each instance broadcasts to local WebSocket connections

### 4. Notifications WebSocket (`app/api/v1/notifications/websocket.py`)

**Endpoint:** `GET /api/v1/notifications/ws?token={jwt}`

**Events Received:**
```json
{
  "event": "notification",
  "data": {
    "id": "notif_123",
    "type": "message|system|alert",
    "title": "New Message",
    "body": "You have a new message",
    "data": {},
    "read": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Badge Update:**
```json
{
  "event": "badge_update",
  "data": {
    "count": 5
  }
}
```

**Events Sent:**

**Mark Read:**
```json
{
  "event": "mark_read",
  "notification_id": "notif_123"
}
```

**Clear All:**
```json
{
  "event": "clear_all"
}
```

## Connection Lifecycle

### 1. Connection Establishment
```
1. Client sends WebSocket handshake with JWT token
2. Server validates token and extracts user_id
3. Server verifies room access
4. Server accepts connection
5. Connection added to manager
6. "user_joined" broadcast to room
7. Join event published to Redis
```

### 2. Message Flow
```
1. Client sends JSON message
2. Server parses event type
3. Handler processes event (message/typing/read/etc.)
4. Handler saves to database (if applicable)
5. Handler publishes to Redis
6. Local connections receive broadcast
7. Other instances receive via Redis pub/sub
8. All instances broadcast to their local connections
```

### 3. Disconnection
```
1. WebSocket disconnect detected
2. "user_left" broadcast to room
3. Leave event published to Redis
4. Connection removed from manager
5. Room cleaned up if empty
```

## Usage Examples

### JavaScript Client

```javascript
// Chat WebSocket
const chatWs = new WebSocket(
  `ws://localhost:8000/api/v1/chat/ws?token=${jwtToken}&room_id=room_123`
);

chatWs.onopen = () => console.log('Connected to chat');

chatWs.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.event) {
    case 'message':
      displayMessage(data.data);
      break;
    case 'typing':
      showTypingIndicator(data.data);
      break;
    case 'user_joined':
      notifyUserJoined(data.data);
      break;
    case 'user_left':
      notifyUserLeft(data.data);
      break;
  }
};

// Send message
chatWs.send(JSON.stringify({
  event: 'message',
  room_id: 'room_123',
  content: 'Hello!',
  type: 'text'
}));

// Send typing indicator
chatWs.send(JSON.stringify({
  event: 'typing',
  room_id: 'room_123'
}));

// Mark message as read
chatWs.send(JSON.stringify({
  event: 'read',
  room_id: 'room_123',
  message_id: 'msg_456'
}));
```

```javascript
// Notifications WebSocket
const notifWs = new WebSocket(
  `ws://localhost:8000/api/v1/notifications/ws?token=${jwtToken}`
);

notifWs.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.event) {
    case 'notification':
      showNotification(data.data);
      updateBadge(data.data);
      break;
    case 'badge_update':
      updateUnreadCount(data.data.count);
      break;
  }
};

// Mark notification as read
notifWs.send(JSON.stringify({
  event: 'mark_read',
  notification_id: 'notif_123'
}));

// Clear all notifications
notifWs.send(JSON.stringify({
  event: 'clear_all'
}));
```

## Redis Configuration

Ensure Redis is running and accessible:

```python
# In app/core/config.py
REDIS_URL = "redis://localhost:6379/0"
```

For production, use:
```python
REDIS_URL = "redis://:password@redis-server:6379/0"
```

Or with Redis Sentinel:
```python
REDIS_URL = "sentinel://:password@sentinel1:26379,sentinel2:26379/mymaster/0"
```

## Scaling Considerations

### Horizontal Scaling
- Multiple FastAPI instances can run behind a load balancer
- Redis pub/sub ensures all instances receive messages
- Each instance maintains its own connection manager
- WebSocket connections are sticky to specific instances

### Load Balancer Configuration
```
WebSocket Upgrade Header → Load Balancer
                                ↓
                     Session Affinity (IP hash or cookie)
                                ↓
                 FastAPI Instance 1, 2, or N
```

### Performance Optimization
1. **Connection Pooling:** Redis connection reused across requests
2. **Message Batching:** Multiple messages can be batched in Redis
3. **Room Sharding:** Large rooms can be split across multiple channels
4. **Connection Limits:** Implement max connections per user/room

## Error Handling

### Connection Errors
```python
# Authentication failure
WebSocketDisconnect(code=1008, reason="Authentication failed")

# Room access denied
WebSocketDisconnect(code=1008, reason="Room access denied")
```

### Message Errors
```json
{
  "event": "error",
  "data": {
    "message": "Error description"
  }
}
```

### Automatic Reconnection
Client should implement exponential backoff:
```javascript
let reconnectDelay = 1000;

function connect() {
  ws = new WebSocket(url);

  ws.onclose = () => {
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      connect();
    }, reconnectDelay);
  };
}
```

## Security

### Authentication
- JWT token validation on connection
- Token expiry checked
- Room access verification

### Authorization
- User must be member of room to join
- Room permissions checked before operations
- Private rooms require explicit access

### Rate Limiting
Implement per-user rate limits:
```python
# Pseudo-code
@limiter.limit("60/minute")
async def websocket_endpoint(...):
    ...
```

## Monitoring

### Metrics to Track
- Active connections count
- Messages per second
- Redis pub/sub latency
- WebSocket reconnection rate
- Error rate by event type

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "websocket_connections": len(manager.active_connections),
        "active_rooms": len(manager.active_rooms),
        "redis_status": "connected" if redis_client else "disconnected"
    }
```

## Testing

### Unit Tests
```python
# Test connection manager
async def test_connection_manager():
    ws = WebSocket()
    conn_id = await manager.connect(ws, "user_1", "room_1")
    assert conn_id in manager.active_connections

    await manager.disconnect(conn_id)
    assert conn_id not in manager.active_connections
```

### Integration Tests
```python
# Test WebSocket endpoint
async def test_websocket_chat(client):
    async with client.websocket_connect(
        "/api/v1/chat/ws?token=xxx&room_id=room_1"
    ) as websocket:
        await websocket.send_json({
            "event": "message",
            "room_id": "room_1",
            "content": "Test",
            "type": "text"
        })

        response = await websocket.receive_json()
        assert response["event"] == "message"
```

## Troubleshooting

### Connection Issues
1. Check JWT token validity
2. Verify Redis is running: `redis-cli ping`
3. Check room access permissions
4. Review logs for errors

### Message Not Received
1. Verify Redis pub/sub is working
2. Check if user is in room
3. Verify channel subscription
4. Check network/firewall settings

### High Memory Usage
1. Monitor connection count
2. Implement connection timeout
3. Clean up stale connections
4. Add max connections limit

## Future Enhancements

1. **Message Persistence:** Store undelivered messages for offline users
2. **Message Encryption:** End-to-end encryption for private rooms
3. **File Sharing:** Upload/download files via WebSocket
4. **Video/Voice:** WebRTC integration for calls
5. **Presence System:** Online/offline/away status
6. **Search:** Full-text search in messages
7. **Reactions:** Emoji reactions to messages
8. **Threads:** Nested message conversations
