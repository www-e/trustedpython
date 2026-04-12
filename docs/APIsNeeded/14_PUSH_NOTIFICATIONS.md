# 14 - Push Notifications & Real-Time APIs

> **Priority:** P1 (High - User Engagement)  
> **Base Path:** `/api/v1/push`  
> **Status:** ✅ COMPLETE  
> **Note:** No push notification UI exists yet - these APIs are for mobile push notifications

---

## Overview

Push notifications keep users engaged when app is closed:
- **Device Registration** - Register FCM/APNs tokens
- **Push Notifications** - Send push to specific users
- **Deep Linking** - Navigate to specific screens from push
- **Real-Time Events** - WebSocket events for live updates

---

## API Endpoints Overview

### Device Management

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/push/devices` | POST | Yes | Register device token |
| 2 | `/push/devices` | GET | Yes | Get registered devices |
| 3 | `/push/devices/{tokenId}` | DELETE | Yes | Unregister device |

### Push Notifications

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 4 | `/push/send` | POST | Server | Send push to user |
| 5 | `/push/send/batch` | POST | Server | Send push to multiple users |
| 6 | `/push/send/topic` | POST | Server | Send push to topic subscribers |

### Real-Time Events

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 7 | `/ws/realtime` | GET | Yes | WebSocket for real-time events |

---

## 1. Register Device

### `POST /api/v1/push/devices`

Register a device for push notifications.

#### Request
```json
{
  "platform": "android | ios (required)",
  "token": "string (FCM/APNs token, required)",
  "device_info": {
    "device_model": "string (e.g., iPhone 15 Pro)",
    "os_version": "string (e.g., iOS 17.2)",
    "app_version": "string (e.g., 1.0.0)"
  }
}
```

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "token_id": "string (UUID)",
    "registered_at": "ISO 8601 datetime"
  }
}
```

---

## 2. Get Registered Devices

### `GET /api/v1/push/devices`

Get all devices registered for the user.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "token_id": "string",
        "platform": "android | ios",
        "device_info": {
          "device_model": "string",
          "os_version": "string",
          "app_version": "string"
        },
        "last_active_at": "ISO 8601 datetime",
        "registered_at": "ISO 8601 datetime"
      }
    ]
  }
}
```

---

## 3. Unregister Device

### `DELETE /api/v1/push/devices/{tokenId}`

Unregister a device (stop sending pushes).

#### Success Response (200)
```json
{
  "success": true,
  "message": "Device unregistered"
}
```

---

## 4. Send Push (Internal API)

### `POST /api/v1/push/send`

Send push notification to a user (used by backend services).

#### Request
```json
{
  "user_id": "string (UUID, required)",
  "title": "string (required)",
  "body": "string (required)",
  "data": {
    "type": "new_message | deal_update | listing_approved | payment_confirmed | security_alert",
    "screen": "string (deep link route)",
    "params": {
      "chat_id": "string | null",
      "deal_id": "string | null",
      "listing_id": "string | null",
      "notification_id": "string | null"
    }
  },
  "priority": "high | normal (default: normal)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "push_id": "string",
    "devices_sent": "number",
    "devices_failed": "number"
  }
}
```

---

## Push Notification Payload Examples

### New Message
```json
{
  "notification": {
    "title": "New Message",
    "body": "Ahmed Mediator sent you a message"
  },
  "data": {
    "type": "new_message",
    "screen": "/chat/{chat_id}/{chat_type}",
    "chat_id": "uuid-here",
    "chat_type": "group"
  }
}
```

### Deal Update
```json
{
  "notification": {
    "title": "Deal Update",
    "body": "Your payment has been confirmed"
  },
  "data": {
    "type": "payment_confirmed",
    "screen": "/main?tab=4",
    "deal_id": "uuid-here"
  }
}
```

### Security Alert
```json
{
  "notification": {
    "title": "Security Alert",
    "body": "New login detected from new device"
  },
  "data": {
    "type": "security_alert",
    "screen": "/security-privacy"
  }
}
```

---

## Deep Link Routes

| Route | Screen | Params |
|-------|--------|--------|
| `/chat/{id}/{type}` | Chat Detail | chat_id, chat_type |
| `/notifications` | Notifications List | - |
| `/main?tab={index}` | Main Shell | tab index (0-4) |
| `/buy/{productId}` | Buy Screen | product_id |
| `/deal/{id}` | Deal Details | deal_id |
| `/listing/{id}` | Listing Details | listing_id |
| `/security-privacy` | Security Settings | - |
| `/profile/{userId}` | User Profile | user_id |

---

## 7. Real-Time WebSocket

### `GET /api/v1/ws/realtime`

WebSocket connection for real-time events.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Auth token |

#### Server → Client Events
```json
// New message
{
  "event": "message:new",
  "data": {
    "message_id": "string",
    "room_id": "string",
    "sender_id": "string",
    "content_preview": "string",
    "timestamp": "ISO 8601"
  }
}

// Deal status change
{
  "event": "deal:updated",
  "data": {
    "deal_id": "string",
    "old_status": "string",
    "new_status": "string",
    "timestamp": "ISO 8601"
  }
}

// Notification
{
  "event": "notification:new",
  "data": {
    "notification_id": "string",
    "title": "string",
    "description": "string",
    "type": "string",
    "timestamp": "ISO 8601"
  }
}

// User online status
{
  "event": "user:online",
  "data": { "user_id": "string" }
}

{
  "event": "user:offline",
  "data": { "user_id": "string" }
}

// Payment confirmed
{
  "event": "payment:confirmed",
  "data": {
    "deal_id": "string",
    "confirmed_at": "ISO 8601"
  }
}

// Listing approved
{
  "event": "listing:approved",
  "data": {
    "listing_id": "string",
    "approved_at": "ISO 8601"
  }
}
```

#### Client → Server Events
```json
// Join channels
{ "event": "subscribe", "channel": "chat:{room_id}" }
{ "event": "subscribe", "channel": "deal:{deal_id}" }
{ "event": "subscribe", "channel": "notifications:{user_id}" }

// Leave channels
{ "event": "unsubscribe", "channel": "chat:{room_id}" }

// Heartbeat
{ "event": "ping" }

// Server responds
{ "event": "pong", "timestamp": "ISO 8601" }
```

---

## Push Notification Triggers

| Trigger | Sent To | Priority |
|---------|---------|----------|
| New message | Recipient(s) | High |
| Deal created | Buyer, Seller, Mediator | Normal |
| Deal status change | All participants | High |
| Payment submitted | Mediator | High |
| Payment confirmed | Buyer, Seller | High |
| Payment rejected | Buyer | High |
| Listing approved | Seller | Normal |
| Listing rejected | Seller | Normal |
| New report | Admins/Moderators | Normal |
| User suspended/banned | Affected user | High |
| Security alert | Affected user | High |
| System announcement | All users | Normal |

---

## FCM/APNs Integration

### Recommended Setup:
1. **Firebase Cloud Messaging (FCM)** for Android
2. **Apple Push Notification Service (APNs)** for iOS
3. Use a unified push service library:
   - Python: `firebase-admin` for FCM
   - Python: `apns2` for APNs
   - Or use a service like OneSignal, Firebase Cloud Messaging HTTP v1 API

### Token Management:
- Store tokens in `device_tokens` table
- Clean up expired tokens (FCM returns `NotRegistered`)
- Update token on app reinstall
- One user can have multiple devices

---

## Security Requirements

- ✅ Device tokens encrypted at rest
- ✅ Push notifications don't contain sensitive data
- ✅ Rate limiting on push sends (prevent spam)
- ✅ WebSocket authentication with short-lived tokens
- ✅ Heartbeat/ping-pong to detect dead connections
- ✅ Automatic reconnection on client side
