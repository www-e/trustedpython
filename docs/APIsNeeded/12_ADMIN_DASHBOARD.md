# 12 - Admin Dashboard APIs

> **Priority:** P0 (Critical - Platform Management)  
> **Base Path:** `/api/v1/admin`  
> **Status:** ✅ COMPLETE  
> **UI Analysis:** No admin UI exists yet - these APIs are for future admin panel

---

## Overview

Admin dashboard manages the entire platform including:
- **User Management** - View, verify, suspend users
- **Listing Moderation** - Approve/reject listings before they go live
- **Deal Oversight** - Monitor deals, resolve disputes
- **Mediator Management** - Verify mediators, assign tiers, monitor performance
- **Content Moderation** - Handle reports, block users
- **Platform Analytics** - Revenue, users, deals metrics
- **System Configuration** - Games, categories, promo banners, FAQ

---

## API Endpoints Overview

### Dashboard Stats

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/admin/dashboard/stats` | GET | Admin | Get dashboard overview |
| 2 | `/admin/dashboard/analytics` | GET | Admin | Get detailed analytics |

### User Management

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 3 | `/admin/users` | GET | Admin | List all users |
| 4 | `/admin/users/{id}` | GET | Admin | Get user details |
| 5 | `/admin/users/{id}/verify` | POST | Admin | Verify user |
| 6 | `/admin/users/{id}/suspend` | POST | Admin | Suspend user |
| 7 | `/admin/users/{id}/unsuspend` | POST | Admin | Unsuspend user |
| 8 | `/admin/users/{id}/ban` | POST | Admin | Ban user permanently |
| 9 | `/admin/users/search` | GET | Admin | Search users |

### Listing Moderation

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 10 | `/admin/listings/pending` | GET | Admin | Get listings awaiting approval |
| 11 | `/admin/listings/{id}/approve` | POST | Admin | Approve listing |
| 12 | `/admin/listings/{id}/reject` | POST | Admin | Reject listing |
| 13 | `/admin/listings/{id}` | DELETE | Admin | Remove listing |
| 14 | `/admin/listings` | GET | Admin | Search/filter all listings |

### Deal Management

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 15 | `/admin/deals` | GET | Admin | Get all deals |
| 16 | `/admin/deals/{id}` | GET | Admin | Get deal details |
| 17 | `/admin/deals/{id}/resolve` | POST | Admin | Resolve dispute |
| 18 | `/admin/deals/{id}/cancel` | POST | Admin | Cancel deal |

### Mediator Management

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 19 | `/admin/mediators` | GET | Admin | List all mediators |
| 20 | `/admin/mediators/{id}` | GET | Admin | Get mediator details |
| 21 | `/admin/mediators/{id}/verify` | POST | Admin | Verify mediator |
| 22 | `/admin/mediators/{id}/update-tier` | POST | Admin | Change mediator tier |
| 23 | `/admin/mediators/{id}/suspend` | POST | Admin | Suspend mediator |
| 24 | `/admin/mediators/applications` | GET | Admin | Get mediator applications |
| 25 | `/admin/mediators/applications/{id}/approve` | POST | Admin | Approve mediator application |
| 26 | `/admin/mediators/applications/{id}/reject` | POST | Admin | Reject mediator application |

### Moderation & Reports

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 27 | `/admin/reports` | GET | Admin | Get user reports |
| 28 | `/admin/reports/{id}` | GET | Admin | Get report details |
| 29 | `/admin/reports/{id}/resolve` | POST | Admin | Resolve report |
| 30 | `/admin/blocked-users` | GET | Admin | Get blocked users |
| 31 | `/admin/blocked-users/{id}/unblock` | POST | Admin | Unblock user |

### Platform Configuration

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 32 | `/admin/games` | GET | Admin | Manage games |
| 33 | `/admin/games` | POST | Admin | Add game |
| 34 | `/admin/games/{id}` | PUT | Admin | Update game |
| 35 | `/admin/categories` | GET | Admin | Manage categories |
| 36 | `/admin/categories` | POST | Admin | Add category |
| 37 | `/admin/promo-banners` | GET | Admin | Manage promo banners |
| 38 | `/admin/promo-banners` | POST | Admin | Create promo banner |
| 39 | `/admin/faq` | GET | Admin | Manage FAQ |
| 40 | `/admin/faq` | POST | Admin | Add FAQ item |

---

## 1. Dashboard Stats

### `GET /api/v1/admin/dashboard/stats`

Get platform overview statistics.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 5000,
      "active_today": 342,
      "new_this_week": 120,
      "verified": 3200,
      "suspended": 45
    },
    "listings": {
      "total": 2500,
      "active": 1800,
      "pending_approval": 35,
      "sold_this_week": 180
    },
    "deals": {
      "total": 8500,
      "active": 230,
      "completed_this_week": 420,
      "disputed": 12,
      "success_rate": 94.5
    },
    "mediators": {
      "total": 150,
      "active": 98,
      "verified": 75,
      "avg_response_time": "8 min"
    },
    "revenue": {
      "this_month": "number (platform fees)",
      "last_month": "number",
      "growth_percentage": "number"
    }
  }
}
```

---

## 2. Dashboard Analytics

### `GET /api/v1/admin/dashboard/analytics?period={period}`

Get detailed analytics for a time period.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Period: day, week, month, year (default: week) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "user_growth": [
      { "date": "2024-01-01", "new_users": 25, "active_users": 300 }
    ],
    "deal_volume": [
      { "date": "2024-01-01", "deals": 45, "completed": 42 }
    ],
    "top_games": [
      { "game": "Valorant", "listings": 500, "deals": 250 },
      { "game": "Fortnite", "listings": 400, "deals": 180 }
    ],
    "top_mediators": [
      {
        "id": "string",
        "name": "string",
        "deals_completed": 150,
        "avg_rating": 4.9
      }
    ],
    "revenue_trend": [
      { "date": "2024-01-01", "amount": "number" }
    ]
  }
}
```

---

## 3. List All Users

### `GET /api/v1/admin/users?status={status}&role={role}&search={query}&page={page}&limit={limit}`

Get all users with filtering.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: active, suspended, banned |
| `role` | string | No | Filter: user, mediator, admin |
| `search` | string | No | Search username/email |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "string",
        "username": "string",
        "email": "string",
        "phone": "string",
        "display_name": "string | null",
        "avatar_url": "string | null",
        "is_verified": "boolean",
        "is_suspended": "boolean",
        "is_banned": "boolean",
        "role": "user | mediator | admin",
        "stats": {
          "total_deals": "number",
          "rating": "number",
          "listings_count": "number"
        },
        "created_at": "ISO 8601 datetime",
        "last_login_at": "ISO 8601 datetime"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 5000 }
  }
}
```

---

## 4. Get User Details

### `GET /api/v1/admin/users/{userId}`

Get full user details for admin review.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "username": "string",
    "email": "string",
    "phone": "string",
    "display_name": "string",
    "avatar_url": "string | null",
    "is_verified": "boolean",
    "is_email_verified": "boolean",
    "is_suspended": "boolean",
    "suspension_reason": "string | null",
    "is_banned": "boolean",
    "ban_reason": "string | null",
    "profile": {
      "bio": "string | null",
      "user_role": "string",
      "member_since": "ISO 8601 date",
      "completed_deals": "number",
      "rating": "number",
      "accounts_sold": "number",
      "bought_count": "number"
    },
    "listings": ["number (count)"],
    "active_deals": ["number (count)"],
    "reports_against": ["number (count)"],
    "login_history": [
      {
        "timestamp": "ISO 8601 datetime",
        "ip_address": "string",
        "device_info": "string",
        "status": "success | failed"
      }
    ],
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601"
  }
}
```

---

## 5. Verify User

### `POST /api/v1/admin/users/{userId}/verify`

Verify a user's account.

#### Request
```json
{
  "notes": "string | null (optional admin note)"
}
```

---

## 6. Suspend User

### `POST /api/v1/admin/users/{userId}/suspend`

Temporarily suspend a user.

#### Request
```json
{
  "reason": "string (required)",
  "duration_days": "number | null (null = indefinite)"
}
```

---

## 7. Ban User

### `POST /api/v1/admin/users/{userId}/ban`

Permanently ban a user.

#### Request
```json
{
  "reason": "string (required)"
}
```

---

## 10. Get Pending Listings

### `GET /api/v1/admin/listings/pending?page={page}&limit={limit}`

Get listings awaiting admin approval.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "listings": [
      {
        "id": "string",
        "title": "string",
        "price": "number",
        "game": "string",
        "seller": {
          "id": "string",
          "username": "string",
          "is_verified": "boolean"
        },
        "status": "pending",
        "image_urls": ["string"],
        "created_at": "ISO 8601 datetime",
        "waiting_hours": "number"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 35 }
  }
}
```

---

## 11. Approve Listing

### `POST /api/v1/admin/listings/{listingId}/approve`

Approve a pending listing.

#### Request
```json
{
  "notes": "string | null"
}
```

---

## 12. Reject Listing

### `POST /api/v1/admin/listings/{listingId}/reject`

Reject a listing with reason.

#### Request
```json
{
  "reason": "string (required)"
}
```

---

## 17. Resolve Deal Dispute

### `POST /api/v1/admin/deals/{dealId}/resolve`

Resolve a disputed deal.

#### Request
```json
{
  "decision": "buyer | seller | refund",
  "resolution_notes": "string (required)",
  "refund_amount": "number | null"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "deal_id": "string",
    "status": "resolved",
    "decision": "string",
    "resolved_at": "ISO 8601 datetime",
    "resolved_by": "string (admin ID)"
  }
}
```

---

## 21. Verify Mediator

### `POST /api/v1/admin/mediators/{mediatorId}/verify`

Verify a mediator (grant verified badge).

#### Request
```json
{
  "notes": "string | null"
}
```

---

## 22. Update Mediator Tier

### `POST /api/v1/admin/mediators/{mediatorId}/update-tier`

Change mediator's tier.

#### Request
```json
{
  "tier": "bronze | silver | gold | elite",
  "reason": "string | null"
}
```

---

## 24. Get Mediator Applications

### `GET /api/v1/admin/mediators/applications?status={status}&page={page}&limit={limit}`

Get pending mediator applications.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "applications": [
      {
        "id": "string",
        "user": {
          "id": "string",
          "username": "string",
          "display_name": "string",
          "avatar_url": "string | null"
        },
        "specialization": "string",
        "experience": "string",
        "payment_methods": [
          { "type": "string", "name": "string" }
        ],
        "bio": "string",
        "status": "pending | approved | rejected",
        "applied_at": "ISO 8601 datetime"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 10 }
  }
}
```

---

## 27. Get Reports

### `GET /api/v1/admin/reports?status={status}&type={type}&page={page}&limit={limit}`

Get user reports for moderation.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: pending, resolved, dismissed |
| `type` | string | No | Filter: user, listing, message, deal |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "string",
        "reporter": {
          "id": "string",
          "username": "string"
        },
        "reported_user": {
          "id": "string",
          "username": "string"
        },
        "type": "user | listing | message | deal",
        "target_id": "string (ID of reported item)",
        "reason": "string",
        "description": "string | null",
        "status": "pending | resolved | dismissed",
        "created_at": "ISO 8601 datetime"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 25 }
  }
}
```

---

## 29. Resolve Report

### `POST /api/v1/admin/reports/{reportId}/resolve`

Mark report as resolved with action taken.

#### Request
```json
{
  "action": "none | warning | suspend | ban | remove_content",
  "notes": "string (required)"
}
```

---

## 32. Manage Games

### `GET /api/v1/admin/games`

Get all games for management.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "games": [
      {
        "id": "string",
        "name": "string",
        "slug": "string",
        "icon_url": "string | null",
        "is_active": "boolean",
        "is_popular": "boolean",
        "active_listings": "number",
        "created_at": "ISO 8601 datetime"
      }
    ]
  }
}
```

### `POST /api/v1/admin/games`

Add a new game.

#### Request
```json
{
  "name": "string (required)",
  "slug": "string (required)",
  "icon_url": "string | null",
  "is_popular": "boolean (default: false)"
}
```

---

## 37. Manage Promo Banners

### `POST /api/v1/admin/promo-banners`

Create a new promotional banner.

#### Request
```json
{
  "title": "string (required)",
  "subtitle": "string | null",
  "image_url": "string (required)",
  "action_url": "string | null",
  "action_text": "string | null",
  "priority": "number (default: 0)",
  "start_date": "ISO 8601 date (required)",
  "end_date": "ISO 8601 date | null"
}
```

---

## Admin Role Permissions

| Permission | Description |
|------------|-------------|
| `admin:dashboard:read` | View dashboard stats |
| `admin:users:read` | View users |
| `admin:users:verify` | Verify users |
| `admin:users:suspend` | Suspend users |
| `admin:users:ban` | Ban users |
| `admin:listings:read` | View listings |
| `admin:listings:approve` | Approve listings |
| `admin:listings:reject` | Reject listings |
| `admin:listings:delete` | Remove listings |
| `admin:deals:read` | View deals |
| `admin:deals:resolve` | Resolve disputes |
| `admin:mediators:read` | View mediators |
| `admin:mediators:verify` | Verify mediators |
| `admin:mediators:update-tier` | Change mediator tier |
| `admin:reports:read` | View reports |
| `admin:reports:resolve` | Resolve reports |
| `admin:config:manage` | Manage games, categories, banners |

---

## Security Requirements

- ✅ All admin endpoints require `admin` role
- ✅ Admin actions logged in audit trail
- ✅ Sensitive actions (ban, resolve dispute) require confirmation
- ✅ Rate limiting on admin endpoints
- ✅ IP whitelist for admin panel access (optional)
- ✅ Two-factor authentication required for admin accounts
