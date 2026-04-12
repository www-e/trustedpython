# 03 - Notifications APIs

> **Priority:** P1 (High - Core Feature)  
> **Base Path:** `/api/v1/notifications`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of notification types, mark as read, empty states

---

## Overview

Notifications system provides real-time alerts to users about account activity, messages, security events, purchases, and system updates.

### Notification Types

| Type | Description | Example |
|------|-------------|---------|
| `account_update` | Account changes | "Your account has been verified" |
| `message` | New messages | "You have a new message from seller_123" |
| `security_alert` | Security events | "New login detected from new device" |
| `purchase` | Transaction updates | "Your purchase has been confirmed" |
| `system` | Platform updates | "Scheduled maintenance on Sunday 2 AM" |

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/notifications` | GET | Yes | Get user notifications |
| 2 | `/notifications/{id}` | GET | Yes | Get single notification |
| 3 | `/notifications/{id}/read` | POST | Yes | Mark notification as read |
| 4 | `/notifications/read-all` | POST | Yes | Mark all as read |
| 5 | `/notifications/unread-count` | GET | Yes | Get unread count |
| 6 | `/notifications/{id}` | DELETE | Yes | Delete notification |
| 7 | `/notifications/settings` | GET | Yes | Get notification preferences |
| 8 | `/notifications/settings` | PUT | Yes | Update notification preferences |
| 9 | `/notifications/ws` | GET | Yes | WebSocket for real-time |

---

## 1. Get Notifications

### `GET /api/v1/notifications?type={type}&is_read={bool}&page={page}&limit={limit}`

Get notifications for the authenticated user.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type |
| `is_read` | boolean | No | Filter by read status |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20, max: 50) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "string (UUID)",
        "title": "string",
        "description": "string",
        "type": "account_update | message | security_alert | purchase | system",
        "is_read": "boolean",
        "icon": "string (icon identifier)",
        "action_url": "string | null",
        "metadata": {
          "sender_id": "string | null",
          "deal_id": "string | null",
          "message_id": "string | null"
        },
        "created_at": "ISO 8601 datetime",
        "relative_time": "string (e.g., '2h ago')"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    },
    "unread_count": 12
  }
}
```

---

## 2. Mark Notification as Read

### `POST /api/v1/notifications/{notificationId}/read`

Mark a single notification as read.

#### Success Response (200)
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

## 3. Mark All as Read

### `POST /api/v1/notifications/read-all`

Mark all notifications as read.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "marked_count": "number"
  }
}
```

---

## 4. Get Unread Count

### `GET /api/v1/notifications/unread-count`

Get the count of unread notifications.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "count": 5
  }
}
```

---

## 5. Delete Notification

### `DELETE /api/v1/notifications/{notificationId}`

Delete a notification.

#### Success Response (200)
```json
{
  "success": true,
  "message": "Notification deleted"
}
```

---

## 6. Get Notification Settings

### `GET /api/v1/notifications/settings`

Get user's notification preferences.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "push_notifications": "boolean",
    "email_notifications": "boolean",
    "types": {
      "account_update": { "enabled": "boolean", "push": "boolean", "email": "boolean" },
      "message": { "enabled": "boolean", "push": "boolean", "email": "boolean" },
      "security_alert": { "enabled": "boolean", "push": "boolean", "email": "boolean" },
      "purchase": { "enabled": "boolean", "push": "boolean", "email": "boolean" },
      "system": { "enabled": "boolean", "push": "boolean", "email": "boolean" }
    }
  }
}
```

---

## 7. Update Notification Settings

### `PUT /api/v1/notifications/settings`

Update notification preferences.

#### Request
```json
{
  "push_notifications": "boolean | null",
  "email_notifications": "boolean | null",
  "types": {
    "account_update": { "enabled": "boolean | null", "push": "boolean | null", "email": "boolean | null" },
    "message": { "enabled": "boolean | null", "push": "boolean | null", "email": "boolean | null" },
    "security_alert": { "enabled": "boolean | null", "push": "boolean | null", "email": "boolean | null" },
    "purchase": { "enabled": "boolean | null", "push": "boolean | null", "email": "boolean | null" },
    "system": { "enabled": "boolean | null", "push": "boolean | null", "email": "boolean | null" }
  }
}
```

---

## 8. WebSocket for Real-Time Notifications

### `GET /api/v1/notifications/ws`

WebSocket connection for push notifications.

#### Server → Client Events
```json
{
  "event": "notification",
  "data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "type": "account_update | message | security_alert | purchase | system",
    "created_at": "ISO 8601"
  }
}
```

---

## Notification Creation Triggers

| Trigger | Type | Sent To |
|---------|------|---------|
| New message | message | Recipient |
| Deal initiated | purchase | Buyer & Seller |
| Payment confirmed | purchase | Seller |
| Account verified | account_update | User |
| Password changed | security_alert | User |
| New login detected | security_alert | User |
| System maintenance | system | All users |
| Mediator assigned | message | All deal participants |

---

## Security Requirements

- ✅ Notifications only accessible by owner
- ✅ Sensitive data masked in notifications
- ✅ WebSocket authentication required
- ✅ Rate limiting on notification creation (prevent spam)
