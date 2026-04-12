# 06 - Listings & Sell Flow APIs

> **Priority:** P0 (Critical - Core Business)  
> **Base Path:** `/api/v1/sell`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of sell listing creation, preview, image upload, category selection

---

## Overview

The Sell Flow allows users to create and manage listings for selling their game accounts. It includes:
1. **Create Listing** - Fill in details, upload images
2. **Preview Listing** - Review before publishing
3. **Publish Listing** - Make it visible in marketplace
4. **Category Selection** - Choose game category
5. **Premium Listings** - Paid promotion with tiers (Regular, Gold, Elite)

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/sell/listings` | POST | Yes | Create new listing |
| 2 | `/sell/listings/preview` | POST | Yes | Preview listing before publish |
| 3 | `/sell/categories` | GET | No | Get available categories |
| 4 | `/sell/games` | GET | No | Get available games |
| 5 | `/sell/upload-image` | POST | Yes | Upload listing images |
| 6 | `/sell/listings/{id}` | PUT | Yes | Update listing |
| 7 | `/sell/listings/{id}/publish` | POST | Yes | Publish draft listing |
| 8 | `/sell/listings/{id}/unpublish` | POST | Yes | Unpublish listing |
| 9 | `/sell/analytics` | GET | Yes | Get sell analytics |

---

## 1. Create Listing

### `POST /api/v1/sell/listings`

Create a new listing (initially as draft).

#### Request
```json
{
  "title": "string (required, 3-100 chars)",
  "price": "number (required, > 0)",
  "game": "string (required)",
  "category_id": "string (UUID, required)",
  "description": "string | null (max 2000 chars)",
  "image_ids": ["string (UUIDs of uploaded images)"],
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
    "category_id": "string",
    "description": "string | null",
    "thumbnail_url": "string | null",
    "image_urls": ["string"],
    "status": "draft | active",
    "is_premium": "boolean",
    "tier": "string | null",
    "created_at": "ISO 8601 datetime"
  }
}
```

#### Error Responses
- **400 Bad Request** - Validation errors
- **400 Bad Request** - No images provided
- **403 Forbidden** - Account not verified

---

## 2. Preview Listing

### `POST /api/v1/sell/listings/preview`

Preview how listing will appear before publishing.

#### Request
```json
{
  "title": "string",
  "price": "number",
  "game": "string",
  "description": "string | null",
  "image_urls": ["string"],
  "is_premium": "boolean",
  "tier": "string | null"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "preview": {
      "title": "string",
      "price": "number",
      "formatted_price": "string (e.g., '$450')",
      "game": "string",
      "thumbnail_url": "string",
      "is_premium": "boolean",
      "tier": "string | null",
      "estimated_views": "number | null"
    }
  }
}
```

---

## 3. Get Categories

### `GET /api/v1/sell/categories`

Get all available listing categories.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "string (UUID)",
        "name": "string",
        "slug": "string",
        "icon": "string (icon identifier)",
        "game": "string | null",
        "description": "string",
        "listing_count": "number"
      }
    ]
  }
}
```

---

## 4. Get Games

### `GET /api/v1/sell/games`

Get all supported games for listings.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "games": [
      {
        "id": "string (UUID)",
        "name": "string",
        "slug": "string",
        "icon_url": "string | null",
        "banner_url": "string | null",
        "active_listings": "number",
        "avg_price": "number | null",
        "popular": "boolean"
      }
    ]
  }
}
```

---

## 5. Upload Image

### `POST /api/v1/sell/upload-image`

Upload images for a listing.

#### Request (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `images` | file[] | Yes | Listing images (max 10) |

#### Constraints
- Max file size per image: 5MB
- Allowed types: jpg, jpeg, png, webp
- Recommended: 1200x800px minimum
- Max images: 10 per listing

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "images": [
      {
        "id": "string (UUID)",
        "url": "string (CDN URL)",
        "thumbnail_url": "string (thumbnail URL)",
        "filename": "string",
        "size": "number (bytes)",
        "width": "number (px)",
        "height": "number (px)"
      }
    ]
  }
}
```

---

## 6. Update Listing

### `PUT /api/v1/sell/listings/{listingId}`

Update an existing draft listing.

#### Request
```json
{
  "title": "string | null",
  "price": "number | null",
  "game": "string | null",
  "description": "string | null",
  "image_ids": ["string"] | null,
  "is_premium": "boolean | null",
  "tier": "string | null"
}
```

---

## 7. Publish Listing

### `POST /api/v1/sell/listings/{listingId}/publish`

Publish a draft listing to make it visible.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "status": "active",
    "published_at": "ISO 8601 datetime"
  }
}
```

---

## 8. Unpublish Listing

### `POST /api/v1/sell/listings/{listingId}/unpublish`

Unpublish a listing (hide from marketplace).

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "id": "string",
    "status": "draft",
    "unpublished_at": "ISO 8601 datetime"
  }
}
```

---

## 9. Sell Analytics

### `GET /api/v1/sell/analytics`

Get analytics for user's listings.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "total_listings": "number",
    "active_listings": "number",
    "sold_listings": "number",
    "total_views": "number",
    "total_revenue": "number",
    "avg_time_to_sell": "number (days)",
    "top_performing_listing": {
      "id": "string",
      "title": "string",
      "views": "number",
      "sold_in_days": "number"
    },
    "recent_activity": [
      {
        "type": "view | inquiry | sale",
        "listing_id": "string",
        "listing_title": "string",
        "timestamp": "ISO 8601 datetime"
      }
    ]
  }
}
```

---

## Listing Status Flow

```
┌─────────────────────────────────────────────┐
│              LISTING LIFECYCLE              │
└─────────────────────────────────────────────┘

  draft ──→ active ──→ sold
   │          │
   │          └──→ expired
   │
   └──→ deleted

Status Explanations:
┌─────────────┬──────────────────────────────────────────────┐
│ draft       │ Created but not yet published                │
│ active      │ Published and visible in marketplace         │
│ sold        │ Account sold, listing marked as completed    │
│ expired     │ Listing expired (e.g., 30 days old)          │
└─────────────┴──────────────────────────────────────────────┘
```

---

## Premium Listing Tiers

| Tier | Price Multiplier | Features |
|------|------------------|----------|
| Regular | 1x | Standard listing |
| Gold | 1.5x | Featured in search, highlighted border |
| Elite | 2x | Top of search, premium badge, push notification |

---

## Security Requirements

- ✅ Only listing owner can edit/delete
- ✅ Image upload scanning for inappropriate content
- ✅ Rate limiting: max 10 new listings/day
- ✅ Price validation (must be > 0)
- ✅ Title/description content moderation
- ✅ Premium tier validation (user must have required permissions)
