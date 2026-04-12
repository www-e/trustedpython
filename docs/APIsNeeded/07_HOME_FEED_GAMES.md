# 07 - Home Feed & Games APIs

> **Priority:** P1 (High - Discovery)  
> **Base Path:** `/api/v1/home`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of home screen, categories, featured accounts, search, FAQ

---

## Overview

The Home Feed is the main discovery interface where users browse accounts. It includes:
- **Featured Accounts** - Curated/premium listings
- **Categories** - Game-based filtering
- **Search** - Full-text search across accounts
- **Promo Sections** - Marketing banners
- **FAQ** - Help content
- **Games** - Browse by game

---

## API Endpoints Overview

### Home Feed

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/home/feed` | GET | No | Get main home feed |
| 2 | `/home/featured` | GET | No | Get featured accounts |
| 3 | `/home/categories` | GET | No | Get all categories |
| 4 | `/home/promo` | GET | No | Get promotional banners |
| 5 | `/home/faq` | GET | No | Get FAQ items |
| 6 | `/home/search` | GET | No | Search accounts |
| 7 | `/home/games` | GET | No | Get all games |
| 8 | `/home/games/{gameId}/accounts` | GET | No | Get accounts for a game |

---

## 1. Get Home Feed

### `GET /api/v1/home/feed?category={category}&game={game}&page={page}&limit={limit}`

Get the main home feed with mixed content.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `game` | string | No | Filter by game name |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "featured_accounts": [
      {
        "id": "string",
        "title": "string",
        "game": "string",
        "price": "number",
        "currency": "string",
        "image_url": "string",
        "rating": "number",
        "reviews": "number",
        "is_premium": "boolean",
        "tier": "gold | elite | null"
      }
    ],
    "accounts": [
      {
        "id": "string",
        "title": "string",
        "game": "string",
        "price": "number",
        "image_url": "string",
        "seller_name": "string",
        "rating": "number",
        "reviews": "number",
        "is_premium": "boolean",
        "tier": "string | null"
      }
    ],
    "categories": [
      {
        "id": "string",
        "name": "string",
        "icon": "string",
        "count": "number"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 500
    }
  }
}
```

---

## 2. Get Featured Accounts

### `GET /api/v1/home/featured?limit={limit}`

Get curated/premium featured accounts.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | int | No | Number of accounts (default: 10, max: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "string",
        "title": "string",
        "game": "string",
        "price": "number",
        "image_url": "string",
        "rating": "number",
        "reviews": "number",
        "tier": "gold | elite",
        "seller": {
          "username": "string",
          "avatar_url": "string | null",
          "rating": "number"
        }
      }
    ]
  }
}
```

---

## 3. Get Categories

### `GET /api/v1/home/categories`

Get all available account categories.

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
        "description": "string",
        "account_count": "number",
        "is_active": "boolean"
      }
    ]
  }
}
```

---

## 4. Get Promo Banners

### `GET /api/v1/home/promo`

Get promotional banners for the home screen.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "banners": [
      {
        "id": "string",
        "title": "string",
        "subtitle": "string | null",
        "image_url": "string",
        "action_url": "string | null",
        "action_text": "string | null",
        "priority": "number",
        "is_active": "boolean",
        "start_date": "ISO 8601 date",
        "end_date": "ISO 8601 date | null"
      }
    ]
  }
}
```

---

## 5. Get FAQ

### `GET /api/v1/home/faq`

Get frequently asked questions.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "faq_items": [
      {
        "id": "string",
        "question": "string",
        "answer": "string",
        "category": "string",
        "order": "number"
      }
    ]
  }
}
```

---

## 6. Search Accounts

### `GET /api/v1/home/search?q={query}&game={game}&price_min={min}&price_max={max}&sort={sort}&page={page}&limit={limit}`

Search accounts with filters.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `game` | string | No | Filter by game |
| `price_min` | number | No | Minimum price |
| `price_max` | number | No | Maximum price |
| `sort` | string | No | Sort: relevance, newest, price_asc, price_desc, rating |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "query": "string",
    "total_results": "number",
    "accounts": [
      {
        "id": "string",
        "title": "string",
        "game": "string",
        "price": "number",
        "image_url": "string",
        "rating": "number",
        "reviews": "number",
        "is_premium": "boolean",
        "tier": "string | null",
        "highlights": ["string (matched text snippets)"]
      }
    ],
    "filters": {
      "available_games": ["string"],
      "price_range": { "min": "number", "max": "number" }
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150
    }
  }
}
```

---

## 7. Get Games

### `GET /api/v1/home/games?sort={sort}&limit={limit}`

Get all supported games.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sort` | string | No | Sort: name, popularity, newest |
| `limit` | int | No | Items per page (default: 50) |

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
        "description": "string | null",
        "active_listings": "number",
        "avg_price": "number | null",
        "is_popular": "boolean",
        "is_trending": "boolean"
      }
    ]
  }
}
```

---

## 8. Get Game Accounts

### `GET /api/v1/home/games/{gameId}/accounts?sort={sort}&page={page}&limit={limit}`

Get accounts for a specific game.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sort` | string | No | Sort: newest, price_asc, price_desc, rating |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 20) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "game": {
      "id": "string",
      "name": "string",
      "icon_url": "string | null"
    },
    "accounts": [
      {
        "id": "string",
        "title": "string",
        "game": "string",
        "price": "number",
        "image_url": "string",
        "rating": "number",
        "reviews": "number",
        "is_premium": "boolean",
        "tier": "string | null",
        "seller": {
          "username": "string",
          "avatar_url": "string | null"
        }
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

## Home Feed Content Structure

```
┌────────────────────────────────────────────────────┐
│                  HOME SCREEN                        │
├────────────────────────────────────────────────────┤
│  1. Header (Logo + Notifications)                  │
│  2. Search Bar                                     │
│  3. Categories (Horizontal Scroll)                 │
│  4. Featured Section (Premium Accounts)            │
│  5. Promo Banner                                   │
│  6. Account Grid (Mixed listings)                  │
│  7. FAQ Section                                    │
└────────────────────────────────────────────────────┘
```

---

## Security Requirements

- ✅ Public endpoints (no auth required)
- ✅ Rate limiting on search (prevent scraping)
- ✅ Content moderation on featured accounts
- ✅ Cache frequently accessed data (Redis)
- ✅ CDN for images and banners
