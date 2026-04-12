# Notifications API Reference

Quick reference for all notification endpoints.

---

## REST Endpoints

### GET /notifications
Get paginated notifications for authenticated user.

**Auth:** Bearer Token Required

**Query Params:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| type | string | No | - | Filter by type (account_update, message, security_alert, purchase, system) |
| is_read | boolean | No | - | Filter by read status |
| page | int | No | 1 | Page number (min: 1) |
| limit | int | No | 20 | Items per page (min: 1, max: 50) |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "uuid",
        "title": "string",
        "description": "string",
        "type": "message",
        "is_read": false,
        "icon": "message",
        "action_url": "/chat/abc",
        "metadata": {},
        "created_at": "2026-04-11T10:00:00Z",
        "relative_time": "2h ago"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    },
    "unread_count": 12
  }
}
```

**Errors:**
- 401: Not authenticated
- 400: Invalid pagination parameters

---

### GET /notifications/{id}
Get single notification by ID.

**Auth:** Bearer Token Required

**Path Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Notification ID |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "string",
    "description": "string",
    "type": "message",
    "is_read": false,
    "icon": "string",
    "action_url": "string | null",
    "metadata": {},
    "created_at": "2026-04-11T10:00:00Z",
    "relative_time": "2h ago"
  }
}
```

**Errors:**
- 401: Not authenticated
- 403: Access denied (not owner)
- 404: Notification not found

---

### POST /notifications/{id}/read
Mark a notification as read.

**Auth:** Bearer Token Required

**Path Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Notification ID |

**Response (200):**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

**Errors:**
- 401: Not authenticated
- 403: Access denied (not owner)
- 404: Notification not found

---

### POST /notifications/read-all
Mark all notifications as read.

**Auth:** Bearer Token Required

**Response (200):**
```json
{
  "success": true,
  "data": {
    "marked_count": 25
  }
}
```

**Errors:**
- 401: Not authenticated

---

### GET /notifications/unread-count
Get count of unread notifications.

**Auth:** Bearer Token Required

**Response (200):**
```json
{
  "success": true,
  "data": {
    "count": 5
  }
}
```

**Errors:**
- 401: Not authenticated

---

### DELETE /notifications/{id}
Delete a notification.

**Auth:** Bearer Token Required

**Path Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Notification ID |

**Response (200):**
```json
{
  "success": true,
  "message": "Notification deleted"
}
```

**Errors:**
- 401: Not authenticated
- 403: Access denied (not owner)
- 404: Notification not found

---

### GET /notifications/settings
Get notification preferences.

**Auth:** Bearer Token Required

**Response (200):**
```json
{
  "success": true,
  "data": {
    "push_notifications": true,
    "email_notifications": true,
    "types": {
      "account_update": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "message": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "security_alert": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "purchase": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "system": {
        "enabled": true,
        "push": true,
        "email": true
      }
    }
  }
}
```

**Errors:**
- 401: Not authenticated

---

### PUT /notifications/settings
Update notification preferences.

**Auth:** Bearer Token Required

**Request Body:**
```json
{
  "push_notifications": true,
  "email_notifications": false,
  "types": {
    "message": {
      "push": false,
      "email": false
    }
  }
}
```

**All fields optional.** Only provided fields will be updated.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "push_notifications": true,
    "email_notifications": false,
    "types": {
      "account_update": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "message": {
        "enabled": true,
        "push": false,
        "email": false
      },
      "security_alert": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "purchase": {
        "enabled": true,
        "push": true,
        "email": true
      },
      "system": {
        "enabled": true,
        "push": true,
        "email": true
      }
    }
  }
}
```

**Errors:**
- 401: Not authenticated
- 400: Invalid settings data

---

## WebSocket Endpoint

### WS /notifications/ws
Real-time notification delivery.

**Auth:** JWT Token via query param

**Query Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | JWT access token |

**Connection URL:**
```
wss://api.example.com/api/v1/notifications/ws?token=YOUR_JWT_TOKEN
```

---

### Server → Client Events

#### notification
New notification received.

```json
{
  "event": "notification",
  "data": {
    "id": "uuid",
    "title": "New message",
    "description": "You have a new message...",
    "type": "message",
    "icon": "message",
    "action_url": "/chat/abc",
    "metadata": {},
    "read": false,
    "created_at": "2026-04-11T10:00:00Z"
  }
}
```

#### badge_update
Unread count updated.

```json
{
  "event": "badge_update",
  "data": {
    "count": 5
  }
}
```

#### notification_read
Notification marked as read.

```json
{
  "event": "notification_read",
  "data": {
    "notification_id": "uuid"
  }
}
```

#### notifications_cleared
All notifications cleared.

```json
{
  "event": "notifications_cleared",
  "data": {}
}
```

#### notification_deleted
Notification deleted.

```json
{
  "event": "notification_deleted",
  "data": {
    "notification_id": "uuid"
  }
}
```

#### error
Error occurred.

```json
{
  "event": "error",
  "data": {
    "message": "Error description"
  }
}
```

---

### Client → Server Events

#### mark_read
Mark notification as read.

```json
{
  "event": "mark_read",
  "notification_id": "uuid"
}
```

#### clear_all
Clear all notifications.

```json
{
  "event": "clear_all"
}
```

---

## Notification Types

| Type | Value | Icon | Description |
|------|-------|------|-------------|
| Account Update | `account_update` | account_circle | Account changes, verification |
| Message | `message` | message | New messages, mediator updates |
| Security Alert | `security_alert` | security | Password changes, new logins |
| Purchase | `purchase` | shopping_cart | Deal updates, payments |
| System | `system` | notifications | Platform updates, maintenance |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Create notification (internal) | 10 per user | 60 seconds |
| All other endpoints | Standard API limits | - |

---

## Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message"
}
```

Or for validation errors:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": {
    "field": ["error1", "error2"]
  }
}
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## cURL Examples

### Get Notifications
```bash
curl -X GET "https://api.example.com/api/v1/notifications?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Mark as Read
```bash
curl -X POST "https://api.example.com/api/v1/notifications/UUID/read" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Unread Count
```bash
curl -X GET "https://api.example.com/api/v1/notifications/unread-count" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Settings
```bash
curl -X PUT "https://api.example.com/api/v1/notifications/settings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "push_notifications": true,
    "email_notifications": false,
    "types": {
      "message": {"push": false}
    }
  }'
```

### Delete Notification
```bash
curl -X DELETE "https://api.example.com/api/v1/notifications/UUID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Python SDK Examples

```python
import httpx

class NotificationsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def get_notifications(
        self,
        type: str = None,
        is_read: bool = None,
        page: int = 1,
        limit: int = 20
    ):
        params = {"page": page, "limit": limit}
        if type:
            params["type"] = type
        if is_read is not None:
            params["is_read"] = is_read

        response = await self.client.get("/notifications", params=params)
        return response.json()

    async def mark_as_read(self, notification_id: str):
        response = await self.client.post(
            f"/notifications/{notification_id}/read"
        )
        return response.json()

    async def mark_all_as_read(self):
        response = await self.client.post("/notifications/read-all")
        return response.json()

    async def get_unread_count(self):
        response = await self.client.get("/notifications/unread-count")
        return response.json()

    async def delete_notification(self, notification_id: str):
        response = await self.client.delete(f"/notifications/{notification_id}")
        return response.json()

    async def get_settings(self):
        response = await self.client.get("/notifications/settings")
        return response.json()

    async def update_settings(self, settings: dict):
        response = await self.client.put(
            "/notifications/settings",
            json=settings
        )
        return response.json()
```

---

## TypeScript SDK Examples

```typescript
class NotificationsClient {
  constructor(
    private baseUrl: string,
    private token: string
  ) {}

  private headers = {
    'Authorization': `Bearer ${this.token}`,
    'Content-Type': 'application/json'
  };

  async getNotifications(params?: {
    type?: string;
    is_read?: boolean;
    page?: number;
    limit?: number;
  }) {
    const response = await fetch(
      `${this.baseUrl}/notifications?${new URLSearchParams(params as any)}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async markAsRead(notificationId: string) {
    const response = await fetch(
      `${this.baseUrl}/notifications/${notificationId}/read`,
      { method: 'POST', headers: this.headers }
    );
    return response.json();
  }

  async markAllAsRead() {
    const response = await fetch(
      `${this.baseUrl}/notifications/read-all`,
      { method: 'POST', headers: this.headers }
    );
    return response.json();
  }

  async getUnreadCount() {
    const response = await fetch(
      `${this.baseUrl}/notifications/unread-count`,
      { headers: this.headers }
    );
    return response.json();
  }

  async deleteNotification(notificationId: string) {
    const response = await fetch(
      `${this.baseUrl}/notifications/${notificationId}`,
      { method: 'DELETE', headers: this.headers }
    );
    return response.json();
  }

  async getSettings() {
    const response = await fetch(
      `${this.baseUrl}/notifications/settings`,
      { headers: this.headers }
    );
    return response.json();
  }

  async updateSettings(settings: any) {
    const response = await fetch(
      `${this.baseUrl}/notifications/settings`,
      {
        method: 'PUT',
        headers: this.headers,
        body: JSON.stringify(settings)
      }
    );
    return response.json();
  }
}
```

---

## Quick Testing

### Using httpie
```bash
# Get notifications
http GET https://api.example.com/api/v1/notifications \
  Authorization:"Bearer YOUR_TOKEN"

# Mark as read
http POST https://api.example.com/api/v1/notifications/UUID/read \
  Authorization:"Bearer YOUR_TOKEN"

# Get unread count
http GET https://api.example.com/api/v1/notifications/unread-count \
  Authorization:"Bearer YOUR_TOKEN"
```

### Using Postman
1. Set base URL: `https://api.example.com/api/v1`
2. Add Authorization header: `Bearer YOUR_TOKEN`
3. Use the endpoints listed above

---

## Support

For issues or questions:
- Check `docs/notifications_implementation_summary.md` for implementation details
- Check `docs/notifications_integration_guide.md` for integration examples
- Review `docs/APIsNeeded/03_NOTIFICATIONS.md` for full API specification
