# 13 - Moderation Tools APIs

> **Priority:** P1 (High - Platform Safety)  
> **Base Path:** `/api/v1/moderation`  
> **Status:** ✅ COMPLETE  
> **Note:** No moderation UI exists in current Flutter app - these APIs are for future moderation tools

---

## Overview

Moderation tools ensure platform safety through:
- **User Reports** - Report suspicious users/listings/messages
- **Content Moderation** - Review and moderate user-generated content
- **Block System** - Users can block other users
- **Automated Filters** - Spam/scam detection
- **Moderation Queue** - Review pending reports and content
- **Moderator Actions** - Warnings, suspensions, bans

---

## API Endpoints Overview

### User Reporting

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/moderation/reports` | POST | Yes | Submit a report |
| 2 | `/moderation/reports/my` | GET | Yes | Get user's submitted reports |
| 3 | `/moderation/reports/{id}` | GET | Yes | Get report details |

### Block System

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 4 | `/moderation/blocks` | GET | Yes | Get blocked users |
| 5 | `/moderation/blocks` | POST | Yes | Block a user |
| 6 | `/moderation/blocks/{userId}` | DELETE | Yes | Unblock a user |

### Content Moderation

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 7 | `/moderation/messages` | GET | Moderator | Get reported messages |
| 8 | `/moderation/messages/{id}` | GET | Moderator | Get message details |
| 9 | `/moderation/messages/{id}/remove` | POST | Moderator | Remove message |

### Moderation Queue

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 10 | `/moderation/queue` | GET | Moderator | Get moderation queue |
| 11 | `/moderation/queue/{id}/action` | POST | Moderator | Take moderation action |

---

## USER REPORTING

### 1. Submit Report

### `POST /api/v1/moderation/reports`

Report a user, listing, message, or deal.

#### Request
```json
{
  "report_type": "user | listing | message | deal (required)",
  "target_id": "string (UUID of reported item, required)",
  "reason": "scam | spam | harassment | inappropriate | fraud | other (required)",
  "description": "string | null (optional details)"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "message": "Report submitted successfully",
  "data": {
    "report_id": "string (UUID)",
    "status": "pending",
    "created_at": "ISO 8601 datetime"
  }
}
```

#### Error Responses
- **400 Bad Request** - Invalid report type or reason
- **400 Bad Request** - Cannot report yourself
- **409 Conflict** - Already reported this item

---

### 2. Get My Reports

### `GET /api/v1/moderation/reports/my?status={status}&page={page}&limit={limit}`

Get reports submitted by the authenticated user.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: pending, resolved, dismissed |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "string",
        "report_type": "user | listing | message | deal",
        "target_id": "string",
        "reason": "string",
        "description": "string | null",
        "status": "pending | resolved | dismissed",
        "resolution": {
          "action_taken": "string | null",
          "resolved_at": "ISO 8601 datetime | null",
          "notes": "string | null"
        },
        "created_at": "ISO 8601 datetime"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 5 }
  }
}
```

---

### 3. Get Report Details

### `GET /api/v1/moderation/reports/{reportId}`

Get details of a specific report.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "reporter": {
      "id": "string",
      "username": "string"
    },
    "reported_user": {
      "id": "string",
      "username": "string",
      "avatar_url": "string | null"
    },
    "report_type": "user | listing | message | deal",
    "target_id": "string",
    "target_details": {
      "title": "string | null",
      "content": "string | null",
      "created_at": "ISO 8601 datetime"
    },
    "reason": "string",
    "description": "string | null",
    "status": "pending | resolved | dismissed",
    "resolution": {
      "action_taken": "string | null",
      "moderator_id": "string | null",
      "resolved_at": "ISO 8601 datetime | null",
      "notes": "string | null"
    },
    "created_at": "ISO 8601 datetime"
  }
}
```

---

## BLOCK SYSTEM

### 4. Get Blocked Users

### `GET /api/v1/moderation/blocks?page={page}&limit={limit}`

Get list of users blocked by the authenticated user.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "blocked_users": [
      {
        "user_id": "string",
        "username": "string",
        "display_name": "string | null",
        "avatar_url": "string | null",
        "blocked_at": "ISO 8601 datetime",
        "reason": "string | null"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 3 }
  }
}
```

---

### 5. Block User

### `POST /api/v1/moderation/blocks`

Block another user.

#### Request
```json
{
  "user_id": "string (UUID, required)",
  "reason": "string | null (optional)"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "message": "User blocked successfully",
  "data": {
    "blocked_user_id": "string",
    "blocked_at": "ISO 8601 datetime"
  }
}
```

#### Error Responses
- **400 Bad Request** - Cannot block yourself
- **409 Conflict** - User already blocked

---

### 6. Unblock User

### `DELETE /api/v1/moderation/blocks/{userId}`

Unblock a previously blocked user.

#### Success Response (200)
```json
{
  "success": true,
  "message": "User unblocked successfully"
}
```

#### Error Responses
- **404 Not Found** - User not in blocked list

---

## CONTENT MODERATION

### 7. Get Reported Messages

### `GET /api/v1/moderation/messages?status={status}&page={page}&limit={limit}`

Get messages that have been reported by users.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: pending, reviewed, removed |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "string",
        "content": "string",
        "sender": {
          "id": "string",
          "username": "string",
          "avatar_url": "string | null"
        },
        "chat_room_id": "string",
        "chat_room_type": "group | private",
        "reports_count": "number",
        "first_reported_at": "ISO 8601 datetime",
        "status": "pending | reviewed | removed",
        "deal_id": "string | null"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 15 }
  }
}
```

---

### 9. Remove Message

### `POST /api/v1/moderation/messages/{messageId}/remove`

Remove an inappropriate message.

#### Request
```json
{
  "reason": "string (required)",
  "notify_sender": "boolean (default: true)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Message removed successfully"
}
```

---

## MODERATION QUEUE

### 10. Get Moderation Queue

### `GET /api/v1/moderation/queue?type={type}&priority={priority}&page={page}&limit={limit}`

Get items pending moderation review.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter: reports, listings, users, messages |
| `priority` | string | No | Filter: high, medium, low |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "type": "report | listing | user | message",
        "priority": "high | medium | low",
        "title": "string",
        "description": "string",
        "reporter": {
          "username": "string"
        } | null,
        "target_user": {
          "username": "string"
        } | null,
        "created_at": "ISO 8601 datetime",
        "waiting_hours": "number"
      }
    ],
    "summary": {
      "total": "number",
      "high_priority": "number",
      "avg_wait_hours": "number"
    },
    "pagination": { "page": 1, "limit": 20, "total": 50 }
  }
}
```

---

### 11. Take Moderation Action

### `POST /api/v1/moderation/queue/{itemId}/action`

Take action on a moderation queue item.

#### Request
```json
{
  "action": "approve | reject | remove | warn | suspend | ban | dismiss",
  "reason": "string (required)",
  "notes": "string | null",
  "duration_hours": "number | null (for suspensions)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Moderation action completed",
  "data": {
    "item_id": "string",
    "action_taken": "string",
    "moderator_id": "string",
    "completed_at": "ISO 8601 datetime"
  }
}
```

---

## Report Reasons Reference

| Reason | Description | Applicable To |
|--------|-------------|---------------|
| `scam` | Fraudulent activity | user, listing, deal |
| `spam` | Unsolicited/repetitive content | user, listing, message |
| `harassment` | Abusive behavior | user, message |
| `inappropriate` | Inappropriate content | listing, message |
| `fraud` | Deceptive practices | user, listing, deal |
| `fake_listing` | Fake or misleading listing | listing |
| `impersonation` | Pretending to be someone else | user |
| `other` | Other reason (with description) | all types |

---

## Block System Behavior

### What Happens When You Block Someone:
1. Blocked user cannot see your listings in search results
2. Blocked user cannot send you messages (in-app)
3. Blocked user cannot join deals you're participating in
4. You won't see their content or messages
5. No notification is sent to the blocked user

### What Doesn't Happen:
1. Block is NOT anonymous (they may infer it)
2. Block does NOT report the user (separate action)
3. Block does NOT affect existing completed deals

---

## Moderation Priority System

| Priority | Criteria | SLA |
|----------|----------|-----|
| **High** | Scam reports, harassment, multiple reporters | 2 hours |
| **Medium** | Single user reports, inappropriate content | 24 hours |
| **Low** | Spam, other reports | 48 hours |

---

## Security Requirements

- ✅ Users can only see their own reports
- ✅ Moderators can only access moderation endpoints
- ✅ Block list is private (not visible to other users)
- ✅ Rate limiting on report submission (prevent spam)
- ✅ Users cannot report the same item twice
- ✅ All moderation actions logged in audit trail
- ✅ Automated scam detection flags suspicious patterns
