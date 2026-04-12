# 08 - Onboarding & Splash APIs

> **Priority:** P2 (Low - Supporting)  
> **Base Path:** `/api/v1/app`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of onboarding flow, splash screen, auth check

---

## Overview

Minimal APIs needed for onboarding and splash. Most logic is client-side.

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/app/config` | GET | No | Get app configuration |
| 2 | `/app/validate-token` | POST | Yes | Validate auth token |
| 3 | `/app/version` | GET | No | Get app version info |
| 4 | `/app/maintenance` | GET | No | Check maintenance status |

---

## 1. Get App Config

### `GET /api/v1/app/config`

Get app-wide configuration.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "onboarding_version": "string",
    "force_update": "boolean",
    "min_version": "string",
    "features": {
      "chat_enabled": "boolean",
      "notifications_enabled": "boolean",
      "premium_listings_enabled": "boolean"
    },
    "limits": {
      "max_images_per_listing": "number",
      "max_listings_per_user": "number",
      "max_message_length": "number"
    }
  }
}
```

---

## 2. Validate Token

### `POST /api/v1/app/validate-token`

Check if current auth token is valid.

#### Headers
```
Authorization: Bearer {access_token}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "is_valid": "boolean",
    "user_id": "string | null",
    "expires_at": "ISO 8601 datetime | null"
  }
}
```

---

## 3. Get App Version

### `GET /api/v1/app/version`

Get current app version and update info.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "current_version": "string",
    "latest_version": "string",
    "update_required": "boolean",
    "update_url": "string | null",
    "release_notes": "string | null"
  }
}
```

---

## 4. Check Maintenance

### `GET /api/v1/app/maintenance`

Check if app is in maintenance mode.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "is_maintenance": "boolean",
    "message": "string | null",
    "estimated_end": "ISO 8601 datetime | null"
  }
}
```
