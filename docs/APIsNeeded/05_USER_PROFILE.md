# 05 - User Profile APIs

> **Priority:** P0 (Critical - Core Feature)  
> **Base Path:** `/api/v1/profile`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of profile screen, stats, listings, trade history

---

## Overview

The Profile system provides user profile management including:
- **User Stats** - Completed deals, rating, accounts sold/bought
- **User Listings** - Accounts the user is selling
- **Trade History** - Historical transactions
- **Profile Editing** - Update user info, avatar

---

## API Endpoints Overview

### Profile

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/profile/me` | GET | Yes | Get current user profile |
| 2 | `/profile/me/stats` | GET | Yes | Get user statistics |
| 3 | `/profile/me/trade-history` | GET | Yes | Get user's trade history |
| 4 | `/profile/update` | PUT | Yes | Update user profile |
| 5 | `/profile/avatar` | POST | Yes | Upload avatar |
| 6 | `/profile/{userId}` | GET | Yes | Get another user's profile |

### Listings

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 7 | `/profile/listings` | GET | Yes | Get user's listings |
| 8 | `/profile/listings` | POST | Yes | Create new listing |
| 9 | `/profile/listings/{id}` | GET | Yes | Get listing details |
| 10 | `/profile/listings/{id}` | PUT | Yes | Update listing |
| 11 | `/profile/listings/{id}` | DELETE | Yes | Delete listing |
| 12 | `/profile/listings/{id}/status` | PUT | Yes | Update listing status |
| 13 | `/profile/listings/upload-image` | POST | Yes | Upload listing image |

---

## PROFILE

### 1. Get Current User Profile

### `GET /api/v1/profile/me`

Get authenticated user's full profile.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "username": "string",
    "email": "string",
    "phone": "string",
    "display_name": "string | null",
    "avatar_url": "string | null",
    "user_role": "string (e.g., Pro Trader)",
    "is_verified": "boolean",
    "member_since": "ISO 8601 date",
    "stats": {
      "completed_deals": 42,
      "rating": 4.9,
      "accounts_sold": 15,
      "bought_count": 27
    },
    "recent_listings": [
      { /* listing object */ }
    ],
    "recent_trades": [
      { /* trade history object */ }
    ]
  }
}
```

---

### 2. Get User Statistics

### `GET /api/v1/profile/me/stats`

Get detailed user statistics.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "completed_deals": 42,
    "rating": 4.9,
    "accounts_sold": 15,
    "bought_count": 27,
    "total_revenue": "number | null",
    "avg_deal_value": "number | null",
    "success_rate": "number (percentage)",
    "response_time_avg": "number (minutes) | null",
    "member_since": "ISO 8601 date"
  }
}
```

---

### 3. Get Trade History

### `GET /api/v1/profile/me/trade-history?status={status}&page={page}&limit={limit}`

Get user's trade history.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: completed, pending, cancelled |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": "string (UUID)",
        "title": "string",
        "price": "number",
        "status": "completed | pending | cancelled",
        "timestamp": "ISO 8601 datetime",
        "game": "string | null",
        "counterparty": {
          "username": "string",
          "avatar_url": "string | null"
        },
        "role": "buyer | seller"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100
    }
  }
}
```

---

### 4. Update User Profile

### `PUT /api/v1/profile/update`

Update user profile information.

#### Request
```json
{
  "display_name": "string | null",
  "phone": "string | null",
  "bio": "string | null",
  "user_role": "string | null"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "display_name": "string",
    "phone": "string",
    "bio": "string | null",
    "updated_at": "ISO 8601 datetime"
  }
}
```

---

### 5. Upload Avatar

### `POST /api/v1/profile/avatar`

Upload profile avatar image.

#### Request (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `avatar` | file | Yes | Profile image |

#### Constraints
- Max file size: 2MB
- Allowed types: jpg, jpeg, png
- Recommended: 300x300px minimum

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "avatar_url": "string (URL)"
  }
}
```

---

### 6. Get Another User's Profile

### `GET /api/v1/profile/{userId}`

Get public profile of another user.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "username": "string",
    "display_name": "string | null",
    "avatar_url": "string | null",
    "user_role": "string | null",
    "is_verified": "boolean",
    "member_since": "ISO 8601 date",
    "stats": {
      "completed_deals": "number",
      "rating": "number",
      "accounts_sold": "number"
    }
  }
}
```

---

## LISTINGS

### 7. Get User's Listings

### `GET /api/v1/profile/listings?status={status}&page={page}&limit={limit}`

Get authenticated user's listings.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: active, sold, expired |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "listings": [
      {
        "id": "string (UUID)",
        "title": "string",
        "price": "number",
        "thumbnail_url": "string | null",
        "game": "string | null",
        "status": "active | sold | expired",
        "views_count": "number",
        "created_at": "ISO 8601 datetime",
        "updated_at": "ISO 8601 datetime"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50
    }
  }
}
```

---

### 8. Create Listing

### `POST /api/v1/profile/listings`

Create a new listing.

#### Request
```json
{
  "title": "string (required)",
  "price": "number (required, > 0)",
  "game": "string (required)",
  "description": "string | null",
  "thumbnail_url": "string | null",
  "image_urls": ["string (URLs)"],
  "is_premium": "boolean (default: false)",
  "tier": "Regular | Gold | Elite | null"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "title": "string",
    "price": "number",
    "game": "string",
    "status": "active",
    "created_at": "ISO 8601 datetime"
  }
}
```

---

### 9. Get Listing Details

### `GET /api/v1/profile/listings/{listingId}`

Get details of a specific listing.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "title": "string",
    "price": "number",
    "game": "string",
    "description": "string | null",
    "thumbnail_url": "string | null",
    "image_urls": ["string"],
    "status": "active | sold | expired",
    "is_premium": "boolean",
    "tier": "string | null",
    "views_count": "number",
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601"
  }
}
```

---

### 10. Update Listing

### `PUT /api/v1/profile/listings/{listingId}`

Update an existing listing.

#### Request
```json
{
  "title": "string | null",
  "price": "number | null",
  "game": "string | null",
  "description": "string | null",
  "is_premium": "boolean | null",
  "tier": "string | null"
}
```

---

### 11. Delete Listing

### `DELETE /api/v1/profile/listings/{listingId}`

Delete a listing.

#### Success Response (200)
```json
{
  "success": true,
  "message": "Listing deleted successfully"
}
```

---

### 12. Update Listing Status

### `PUT /api/v1/profile/listings/{listingId}/status`

Update listing status (e.g., mark as sold).

#### Request
```json
{
  "status": "active | sold | expired"
}
```

---

### 13. Upload Listing Image

### `POST /api/v1/profile/listings/upload-image`

Upload an image for a listing.

#### Request (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | Yes | Listing image |

#### Constraints
- Max file size: 5MB
- Allowed types: jpg, jpeg, png
- Max images per listing: 10

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "url": "string (URL)",
    "filename": "string",
    "size": "number (bytes)"
  }
}
```

---

## Data Models

### UserStatsModel
```json
{
  "completed_deals": 42,
  "rating": 4.9,
  "accounts_sold": 15,
  "bought_count": 27
}
```

### ListingModel
```json
{
  "id": "string",
  "title": "string",
  "price": "number",
  "thumbnail_url": "string | null",
  "game": "string | null",
  "status": "active | sold | expired"
}
```

### TradeHistoryModel
```json
{
  "id": "string",
  "title": "string",
  "price": "number",
  "status": "completed | pending | cancelled",
  "timestamp": "ISO 8601 datetime",
  "game": "string | null"
}
```

---

## Security Requirements

- ✅ Users can only edit their own profile
- ✅ Users can only manage their own listings
- ✅ Image upload scanning for malware
- ✅ Rate limiting on listing creation (max 10/day)
- ✅ Trade history only visible to participants
- ✅ Public profiles hide sensitive data (email, phone)
