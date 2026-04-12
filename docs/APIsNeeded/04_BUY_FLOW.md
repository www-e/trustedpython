# 04 - Buy Flow APIs

> **Priority:** P0 (Critical - Core Business)  
> **Base Path:** `/api/v1/buy`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of buy accounts, account details, mediator selection, payment, waiting states

---

## Overview

The Buy Flow is the core business logic of the platform. It involves:
1. **Browse accounts** - Search, filter, sort available accounts
2. **View details** - Account info, images, seller details
3. **Choose mediator** - Select trusted mediator for transaction
4. **Payment** - Upload payment screenshot, confirm with mediator
5. **Waiting** - Await mediator verification
6. **Success** - Deal completed, ownership transferred

---

## API Endpoints Overview

### Accounts

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/buy/accounts` | GET | No | Browse available accounts |
| 2 | `/buy/accounts/{id}` | GET | No | Get account details |
| 3 | `/buy/accounts/{id}/similar` | GET | No | Get similar accounts |

### Mediators

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 4 | `/buy/mediators` | GET | No | List available mediators |
| 5 | `/buy/mediators/{id}` | GET | No | Get mediator profile |
| 6 | `/buy/mediators/{id}/reviews` | GET | No | Get mediator reviews |
| 7 | `/buy/mediators/search` | GET | No | Search mediators |

### Deals

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 8 | `/buy/deals` | POST | Yes | Create a deal (request to buy) |
| 9 | `/buy/deals/{id}` | GET | Yes | Get deal details |
| 10 | `/buy/deals/{id}/status` | PUT | Yes | Update deal status |
| 11 | `/buy/deals/my` | GET | Yes | Get user's deals |

### Payments

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 12 | `/buy/deals/{id}/payment` | POST | Yes | Submit payment (screenshot) |
| 13 | `/buy/deals/{id}/payment/confirm` | POST | Yes | Mediator confirm payment |
| 14 | `/buy/deals/{id}/payment/reject` | POST | Yes | Mediator reject payment |
| 15 | `/buy/deals/{id}/payment/status` | GET | Yes | Check payment status |

---

## ACCOUNTS

### 1. Browse Accounts

### `GET /api/v1/buy/accounts?game={game}&price_min={min}&price_max={max}&level={level}&search={query}&sort={sort}&page={page}&limit={limit}`

Search and filter available game accounts.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `game` | string | No | Filter by game name |
| `price_min` | number | No | Minimum price |
| `price_max` | number | No | Maximum price |
| `level` | string | No | Filter by level/rank |
| `search` | string | No | Full-text search |
| `sort` | string | No | Sort: "newest", "price_asc", "price_desc", "rating" |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "string (UUID)",
        "title": "string",
        "game": "string",
        "rank": "string",
        "price": "number",
        "currency": "string (default: EGP)",
        "seller_id": "string",
        "seller": "string (username)",
        "seller_avatar": "string (URL) | null",
        "rating": "number (0-5)",
        "reviews_count": "number",
        "description": "string",
        "images": ["string (URLs)"],
        "features": [
          {
            "icon": "string (icon identifier)",
            "label": "string"
          }
        ],
        "is_verified": "boolean",
        "is_featured": "boolean",
        "created_at": "ISO 8601 datetime"
      }
    ],
    "filters": {
      "available_games": ["Valorant", "Genshin Impact", "Fortnite"],
      "price_ranges": [
        { "label": "Under $100", "min": 0, "max": 100 },
        { "label": "$100 - $300", "min": 100, "max": 300 },
        { "label": "$300 - $500", "min": 300, "max": 500 },
        { "label": "Over $500", "min": 500, "max": null }
      ],
      "available_levels": ["Radiant", "Immortal", "Diamond", "Platinum"]
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 500,
      "total_pages": 25
    }
  }
}
```

---

### 2. Account Details

### `GET /api/v1/buy/accounts/{accountId}`

Get full details of a game account.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "title": "string",
    "game": "string",
    "rank": "string",
    "price": "number",
    "currency": "string",
    "seller": {
      "id": "string",
      "username": "string",
      "display_name": "string",
      "avatar_url": "string | null",
      "is_online": "boolean",
      "rating": "number",
      "total_sales": "number",
      "member_since": "ISO 8601 date"
    },
    "rating": "number",
    "reviews_count": "number",
    "description": "string",
    "images": ["string"],
    "features": [
      { "icon": "string", "label": "string" }
    ],
    "is_verified": "boolean",
    "is_featured": "boolean",
    "is_available": "boolean",
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601"
  }
}
```

---

### 3. Similar Accounts

### `GET /api/v1/buy/accounts/{accountId}/similar?limit={limit}`

Get similar accounts based game, price, or rank.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "accounts": [
      { /* same structure as browse accounts */ }
    ]
  }
}
```

---

## MEDIATORS

### 4. List Mediators

### `GET /api/v1/buy/mediators?specialization={game}&sort={sort}&page={page}&limit={limit}`

Get available mediators.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialization` | string | No | Filter by game specialty |
| `sort` | string | No | Sort: "rating", "transactions", "tier" |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "mediators": [
      {
        "id": "string (UUID)",
        "name": "string",
        "avatar": "string (URL)",
        "rating": "number (0-5)",
        "program_rating": "number (0-5)",
        "transactions_count": "number",
        "specialization": "string",
        "payment_methods": [
          {
            "type": "bank | wallet | crypto",
            "name": "string (e.g., Bank Transfer, Vodafone Cash)",
            "icon": "string (icon identifier)",
            "details": "string"
          }
        ],
        "response_time": "string (e.g., '5 min')",
        "is_online": "boolean",
        "tier": "bronze | silver | gold | elite",
        "is_verified": "boolean",
        "badges": [
          {
            "id": "string",
            "name": "string (e.g., Top Mediator)",
            "icon": "string (icon identifier)",
            "description": "string",
            "earned_at": "ISO 8601 datetime"
          }
        ],
        "bio": "string"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50,
      "total_pages": 3
    }
  }
}
```

---

### 5. Mediator Profile

### `GET /api/v1/buy/mediators/{mediatorId}`

Get full mediator profile.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "avatar": "string",
    "rating": "number",
    "program_rating": "number",
    "transactions_count": "number",
    "success_rate": "number (percentage)",
    "specialization": "string",
    "payment_methods": [ /* same as list */ ],
    "response_time": "string",
    "is_online": "boolean",
    "tier": "bronze | silver | gold | elite",
    "is_verified": "boolean",
    "badges": [ /* same as list */ ],
    "bio": "string",
    "stats": {
      "total_deals": "number",
      "successful_deals": "number",
      "failed_deals": "number",
      "avg_response_time": "number (minutes)",
      "member_since": "ISO 8601 date"
    }
  }
}
```

---

### 6. Mediator Reviews

### `GET /api/v1/buy/mediators/{mediatorId}/reviews?page={page}&limit={limit}`

Get reviews for a specific mediator.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": "string",
        "reviewer": {
          "username": "string",
          "avatar": "string | null"
        },
        "rating": "number (1-5)",
        "comment": "string",
        "deal_id": "string",
        "created_at": "ISO 8601 datetime"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 50 },
    "average_rating": "number"
  }
}
```

---

## DEALS

### 8. Create Deal

### `POST /api/v1/buy/deals`

Create a new deal (request to buy an account).

#### Request
```json
{
  "account_id": "string (required)",
  "mediator_id": "string (required)",
  "quantity": "number (default: 1)",
  "notes": "string | null"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "status": "pending",
    "account": {
      "id": "string",
      "title": "string",
      "price": "number",
      "game": "string"
    },
    "mediator": {
      "id": "string",
      "name": "string",
      "avatar": "string"
    },
    "buyer_id": "string",
    "seller_id": "string",
    "total_amount": "number",
    "created_at": "ISO 8601 datetime",
    "chat_room_id": "string"
  }
}
```

---

### 9. Get Deal Details

### `GET /api/v1/buy/deals/{dealId}`

Get details of a specific deal.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "status": "pending | awaiting_payment | payment_submitted | verified | completed | cancelled | disputed",
    "account": {
      "id": "string",
      "title": "string",
      "game": "string",
      "price": "number",
      "images": ["string"]
    },
    "mediator": {
      "id": "string",
      "name": "string",
      "avatar": "string",
      "rating": "number"
    },
    "buyer": {
      "id": "string",
      "username": "string",
      "display_name": "string"
    },
    "seller": {
      "id": "string",
      "username": "string",
      "display_name": "string"
    },
    "total_amount": "number",
    "payment": {
      "status": "pending | submitted | verified | rejected",
      "screenshot_url": "string | null",
      "submitted_at": "ISO 8601 | null",
      "verified_at": "ISO 8601 | null"
    },
    "chat_room_id": "string",
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601",
    "completed_at": "ISO 8601 | null"
  }
}
```

---

### 10. Update Deal Status

### `PUT /api/v1/buy/deals/{dealId}/status`

Update deal status (mediator action).

#### Request
```json
{
  "status": "awaiting_payment | payment_submitted | verified | completed | cancelled | disputed",
  "notes": "string | null"
}
```

---

### 11. Get My Deals

### `GET /api/v1/buy/deals/my?role={role}&status={status}&page={page}&limit={limit}`

Get authenticated user's deals.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | string | No | Filter by role: "buyer" or "seller" |
| `status` | string | No | Filter by deal status |

---

## PAYMENTS

### 12. Submit Payment

### `POST /api/v1/buy/deals/{dealId}/payment`

Submit payment with screenshot.

#### Request (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `screenshot` | file | Yes | Payment screenshot |
| `notes` | string | No | Additional notes |

#### Constraints
- Max file size: 5MB
- Allowed types: jpg, jpeg, png

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "deal_id": "string",
    "status": "payment_submitted",
    "screenshot_url": "string",
    "submitted_at": "ISO 8601 datetime"
  }
}
```

---

### 13. Confirm Payment (Mediator)

### `POST /api/v1/buy/deals/{dealId}/payment/confirm`

Mediator confirms payment received.

#### Request
```json
{
  "notes": "string | null"
}
```

---

### 14. Reject Payment (Mediator)

### `POST /api/v1/buy/deals/{dealId}/payment/reject`

Mediator rejects payment (e.g., invalid screenshot).

#### Request
```json
{
  "reason": "string (required)"
}
```

---

### 15. Check Payment Status

### `GET /api/v1/buy/deals/{dealId}/payment/status`

Poll for payment status updates (used in waiting screen).

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "deal_id": "string",
    "status": "pending | submitted | verified | rejected",
    "submitted_at": "ISO 8601 | null",
    "verified_at": "ISO 8601 | null",
    "rejection_reason": "string | null"
  }
}
```

---

## Deal Status Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        DEAL LIFECYCLE                            │
└──────────────────────────────────────────────────────────────────┘

  pending ──→ awaiting_payment ──→ payment_submitted ──→ verified ──→ completed
     │              │                      │                  │
     │              │                      │                  └──→ disputed
     │              │                      │
     │              │                      └──→ rejected ──→ payment_resubmitted
     │              │
     └── cancelled  └── cancelled

Status Explanations:
┌─────────────────────┬────────────────────────────────────────────────┐
│ pending             │ Deal created, waiting for buyer to pay         │
│ awaiting_payment    │ Buyer acknowledged, ready to pay               │
│ payment_submitted   │ Buyer uploaded payment screenshot              │
│ verified            │ Mediator verified payment                      │
│ completed           │ Deal finished, account transferred             │
│ cancelled           │ Deal cancelled by any party                    │
│ disputed            │ Dispute raised, needs resolution               │
│ rejected            │ Payment rejected by mediator                   │
└─────────────────────┴────────────────────────────────────────────────┘
```

---

## Security Requirements

- ✅ Only deal participants can access deal details
- ✅ Payment screenshots encrypted at rest
- ✅ Price cannot be modified after deal creation
- ✅ Mediator must be verified to facilitate deals
- ✅ Rate limiting on deal creation
- ✅ File upload scanning for payment screenshots
- ✅ Audit log for all deal status changes
- ✅ Dispute resolution mechanism
