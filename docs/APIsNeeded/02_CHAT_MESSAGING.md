# 02 - Chat & Messaging APIs

> **Priority:** P0 (Critical - Core Feature)  
> **Base Path:** `/api/v1/chat`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of chat list, chat detail, message bubbles

---

## Overview

The chat system supports two types of conversations:
- **Group Chats** - Multi-participant chats for deals (buyer + seller + mediator)
- **Private Chats** - One-on-one chats (usually user + mediator)

**Real-time delivery via WebSockets or Server-Sent Events (SSE).**

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Type | Description |
|---|----------|--------|------|------|-------------|
| 1 | `/chat/rooms` | GET | Yes | REST | Get user's chat rooms |
| 2 | `/chat/rooms/{id}` | GET | Yes | REST | Get single chat room details |
| 3 | `/chat/rooms/{id}/messages` | GET | Yes | REST | Get messages for a chat |
| 4 | `/chat/rooms/{id}/messages` | POST | Yes | REST | Send a message |
| 5 | `/chat/rooms/{id}/read` | POST | Yes | REST | Mark chat as read |
| 6 | `/chat/rooms/{id}/typing` | POST | Yes | WS | Typing indicator |
| 7 | `/chat/rooms/{id}` | DELETE | Yes | REST | Leave/delete chat |
| 8 | `/chat/ws` | GET | Yes | WS | WebSocket connection |
| 9 | `/chat/upload` | POST | Yes | REST | Upload message attachment |

---

## 1. Get Chat Rooms

### `GET /api/v1/chat/rooms?type={type}&page={page}&limit={limit}`

Get all chat rooms for the authenticated user.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter: "group" or "private" |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20, max: 50) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "rooms": [
      {
        "id": "string (UUID)",
        "name": "string (group name or other user name)",
        "avatar": "string (URL) | null",
        "type": "group | private",
        "participants": [
          {
            "id": "string",
            "username": "string",
            "display_name": "string",
            "avatar_url": "string | null",
            "is_online": "boolean"
          }
        ],
        "last_message": {
          "id": "string",
          "sender_id": "string",
          "sender_name": "string",
          "content": "string",
          "type": "text | image | system",
          "timestamp": "ISO 8601 datetime"
        },
        "unread_count": "number",
        "last_message_time": "ISO 8601 datetime",
        "is_active": "boolean",
        "created_at": "ISO 8601 datetime"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

---

## 2. Get Chat Room Details

### `GET /api/v1/chat/rooms/{roomId}`

Get details of a specific chat room.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `roomId` | string | Yes | Chat room ID |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "avatar": "string | null",
    "type": "group | private",
    "participants": [
      {
        "id": "string",
        "username": "string",
        "display_name": "string",
        "avatar_url": "string | null",
        "role": "admin | member",
        "is_online": "boolean",
        "last_seen_at": "ISO 8601 datetime | null"
      }
    ],
    "created_at": "ISO 8601 datetime",
    "metadata": {
      "deal_id": "string | null",
      "account_id": "string | null"
    }
  }
}
```

---

## 3. Get Messages

### `GET /api/v1/chat/rooms/{roomId}/messages?before={timestamp}&limit={limit}`

Get messages for a specific chat room.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `roomId` | string | Yes | Chat room ID |

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `before` | datetime | No | Get messages before this timestamp (for pagination) |
| `limit` | int | No | Number of messages (default: 50, max: 100) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "string (UUID)",
        "sender_id": "string",
        "sender_name": "string",
        "sender_avatar": "string | null",
        "content": "string",
        "type": "text | image | system",
        "timestamp": "ISO 8601 datetime",
        "is_read": "boolean",
        "attachments": [
          {
            "id": "string",
            "url": "string",
            "filename": "string",
            "size": "number (bytes)",
            "mime_type": "string"
          }
        ]
      }
    ],
    "has_more": "boolean"
  }
}
```

---

## 4. Send Message

### `POST /api/v1/chat/rooms/{roomId}/messages`

Send a message to a chat room.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `roomId` | string | Yes | Chat room ID |

#### Request
```json
{
  "content": "string (message text, required)",
  "type": "text | image | system (default: text)",
  "reply_to_message_id": "string | null"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "sender_id": "string",
    "sender_name": "string",
    "content": "string",
    "type": "text | image | system",
    "timestamp": "ISO 8601 datetime",
    "is_read": false
  }
}
```

#### Error Responses
- **400 Bad Request** - Empty message
- **403 Forbidden** - Not a participant in this chat
- **404 Not Found** - Chat room not found

---

## 5. Mark Chat as Read

### `POST /api/v1/chat/rooms/{roomId}/read`

Mark all messages in a chat as read.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "messages_marked_read": "number"
  }
}
```

---

## 6. WebSocket Connection

### `GET /api/v1/chat/ws`

Establish WebSocket connection for real-time messaging.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token |

#### Client → Server Events
```json
// Join room
{ "event": "join_room", "room_id": "string" }

// Leave room
{ "event": "leave_room", "room_id": "string" }

// Send message
{ "event": "message", "room_id": "string", "content": "string", "type": "text|image" }

// Typing indicator
{ "event": "typing", "room_id": "string" }

// Mark message as read
{ "event": "read", "room_id": "string", "message_id": "string" }
```

#### Server → Client Events
```json
// New message
{
  "event": "message",
  "data": {
    "id": "string",
    "sender_id": "string",
    "sender_name": "string",
    "content": "string",
    "type": "text | image | system",
    "timestamp": "ISO 8601",
    "room_id": "string"
  }
}

// Typing indicator
{ "event": "typing", "data": { "user_id": "string", "room_id": "string" } }

// Message read
{ "event": "read", "data": { "user_id": "string", "message_id": "string" } }

// User joined
{ "event": "user_joined", "data": { "user_id": "string", "room_id": "string" } }

// User left
{ "event": "user_left", "data": { "user_id": "string", "room_id": "string" } }

// Error
{ "event": "error", "data": { "message": "string" } }
```

---

## 7. Upload Attachment

### `POST /api/v1/chat/upload`

Upload a file to be sent as a message attachment.

#### Request (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Image/document file |
| `room_id` | string | Yes | Target chat room |

#### Constraints
- Max file size: 10MB
- Allowed types: jpg, jpeg, png, gif, pdf, doc, docx

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "url": "string",
    "filename": "string",
    "size": "number",
    "mime_type": "string"
  }
}
```

---

## Data Models

### Message Types
| Type | Description |
|------|-------------|
| `text` | Plain text message |
| `image` | Image attachment |
| `system` | System notification (e.g., "User joined") |

### Chat Types
| Type | Description |
|------|-------------|
| `group` | Multi-participant deal chat |
| `private` | One-on-one chat |

---

## Chat Creation Flow (Deal Context)

```
┌─────────────────────────────────────────────────────────────┐
│  When a buyer clicks "Request to Buy" on an account:        │
└─────────────────────────────────────────────────────────────┘

1. Backend creates a new chat room
2. Adds buyer, seller, and mediator as participants
3. Sends system message: "Deal #1234 started"
4. Returns room_id to client
5. Client navigates to chat screen with room_id
```

---

## Security Requirements

- ✅ Only participants can access chat room
- ✅ Messages encrypted at rest
- ✅ Rate limiting: 100 messages/minute per user
- ✅ File upload scanning for malware
- ✅ WebSocket authentication with short-lived tokens
- ✅ Message content sanitization (XSS prevention)
- ✅ Audit log for all messages
