# Home Feed Module Implementation

## Overview

The Home Feed module provides the main discovery interface for the Game Account Marketplace. It includes 8 public endpoints for browsing, searching, and discovering game accounts.

## Architecture

### Directory Structure
```
app/
├── api/v1/home/
│   ├── __init__.py          # Module initialization
│   └── routes.py            # API endpoints (8 routes)
├── schemas/
│   └── home.py              # Pydantic schemas for all responses
├── services/
│   ├── home_service.py      # Business logic layer
│   └── cache_service.py     # Redis caching layer
└── models/
    ├── account.py           # Account model
    └── content.py           # Game, Category, PromoBanner, FAQItem models
```

## API Endpoints

### 1. GET `/api/v1/home/feed` - Main Home Feed
**Purpose:** Get the complete home feed with mixed content

**Query Parameters:**
- `category` (optional): Filter by category
- `game` (optional): Filter by game name
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "featured_accounts": [...],  // Featured/premium accounts
    "accounts": [...],           // Regular account listings
    "categories": [...],         // Available categories
    "pagination": {...}          // Pagination metadata
  }
}
```

### 2. GET `/api/v1/home/featured` - Featured Accounts
**Purpose:** Get curated premium accounts

**Query Parameters:**
- `limit` (default: 10, max: 20): Number of accounts

**Response:**
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "uuid",
        "title": "Account title",
        "game": "PUBG",
        "price": 1500.00,
        "tier": "gold",
        "seller": {...}
      }
    ]
  }
}
```

### 3. GET `/api/v1/home/categories` - Categories
**Purpose:** Get all available account categories

**Response:**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "uuid",
        "name": "Action Games",
        "slug": "action-games",
        "icon": "action",
        "account_count": 150
      }
    ]
  }
}
```

### 4. GET `/api/v1/home/promo` - Promo Banners
**Purpose:** Get active promotional banners

**Response:**
```json
{
  "success": true,
  "data": {
    "banners": [
      {
        "id": "uuid",
        "title": "Summer Sale",
        "subtitle": "Up to 50% off",
        "image_url": "https://...",
        "action_url": "https://...",
        "priority": 10
      }
    ]
  }
}
```

### 5. GET `/api/v1/home/faq` - FAQ Items
**Purpose:** Get frequently asked questions

**Response:**
```json
{
  "success": true,
  "data": {
    "faq_items": [
      {
        "id": "uuid",
        "question": "How do I buy an account?",
        "answer": "Browse accounts...",
        "category": "Buying",
        "order": 1
      }
    ]
  }
}
```

### 6. GET `/api/v1/home/search` - Search Accounts
**Purpose:** Full-text search with filters

**Query Parameters:**
- `q` (required): Search query (min 2 chars)
- `game` (optional): Filter by game
- `price_min` (optional): Minimum price
- `price_max` (optional): Maximum price
- `sort` (default: relevance): Sort order
- `page` (default: 1): Page number
- `limit` (default: 20): Items per page

**Rate Limiting:** 30 requests/minute

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "PUBG account",
    "total_results": 42,
    "accounts": [
      {
        "id": "uuid",
        "title": "PUBG Mobile Elite Account",
        "highlights": ["Matched in title: ...", "Game: PUBG"]
      }
    ],
    "filters": {
      "available_games": ["PUBG", "Fortnite"],
      "price_range": {"min": 50, "max": 5000}
    },
    "pagination": {...}
  }
}
```

### 7. GET `/api/v1/home/games` - Get Games
**Purpose:** Get all supported games

**Query Parameters:**
- `sort` (default: name): Sort by name, popularity, or newest
- `limit` (default: 50, max: 100): Max games to return

**Response:**
```json
{
  "success": true,
  "data": {
    "games": [
      {
        "id": "uuid",
        "name": "PUBG Mobile",
        "slug": "pubg-mobile",
        "icon_url": "https://...",
        "active_listings": 250,
        "avg_price": 850.00,
        "is_popular": true,
        "is_trending": true
      }
    ]
  }
}
```

### 8. GET `/api/v1/home/games/{gameId}/accounts` - Game Accounts
**Purpose:** Get accounts for a specific game

**Path Parameters:**
- `gameId`: Game UUID

**Query Parameters:**
- `sort` (default: newest): Sort order
- `page` (default: 1): Page number
- `limit` (default: 20): Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "game": {
      "id": "uuid",
      "name": "PUBG Mobile",
      "icon_url": "https://..."
    },
    "accounts": [...],
    "pagination": {...}
  }
}
```

## Caching Strategy

### Redis Cache Implementation

**CacheService** (`app/services/cache_service.py`) provides Redis caching for frequently accessed data:

#### Cache TTL (Time To Live)
- **Featured Accounts**: 6 hours
- **Categories**: 24 hours
- **Games**: 24 hours
- **Promo Banners**: 1 hour
- **FAQ**: 24 hours

#### Cache Invalidation
Cache is invalidated on:
- Content updates (admin operations)
- Manual cache clearing via `invalidate_all_home_cache()`

#### Cache Keys
```
home:featured:accounts
home:categories
home:games:{sort}
home:promo:banners
home:faq
```

### Cache Flow

1. **Read Request**: Check Redis cache first
2. **Cache Hit**: Return cached data immediately
3. **Cache Miss**: Query database, cache results, return data
4. **Write Operation**: Invalidate relevant cache keys

## Security Features

### Rate Limiting
- **Search endpoint**: 30 requests/minute per IP
- Implemented using `slowapi` library
- Prevents scraping and abuse

### Public Access
- All endpoints are public (no authentication required)
- Optimized for anonymous browsing
- Sensitive data (seller email, phone) never exposed

### Input Validation
- Query length validation (min 2 characters for search)
- Price range validation (non-negative)
- Pagination limits enforced
- UUID validation for game IDs

## Data Models

### AccountCard
Used across multiple endpoints for consistent account display:
- `id`: Account UUID
- `title`: Account title
- `game`: Game name
- `price`: Listing price
- `image_url`: Primary image
- `rating`: Average rating (0-5)
- `reviews`: Number of reviews
- `is_premium`: Premium listing flag
- `tier`: Account tier (gold/elite/null)
- `seller_name`: Seller username
- `rank`: Account rank/level

### FeaturedAccountCard
Extends AccountCard with:
- `tier`: Always gold or elite
- `seller`: Seller info object

### SearchAccountCard
Extends AccountCard with:
- `highlights`: Matched text snippets

## Database Queries

### Optimized Queries

1. **Featured Accounts**
   - Filters: `status='active'` AND `is_featured=true`
   - Order: `is_verified DESC`, `created_at DESC`
   - Limit: Configurable (max 20)

2. **Search**
   - Full-text search across: title, game, description, rank
   - Dynamic filters: game, price range
   - Multiple sort options
   - Highlight generation for matched text

3. **Game Accounts**
   - Join with images and features
   - Filter by game name
   - Pagination support
   - Seller info eager loading

## Performance Optimization

### Database Indexes
```sql
-- Account indexes
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_game ON accounts(game);
CREATE INDEX idx_accounts_price ON accounts(price);
CREATE INDEX idx_accounts_featured ON accounts(is_featured);

-- Content indexes
CREATE INDEX idx_categories_active ON categories(is_active);
CREATE INDEX idx_games_popular ON games(is_popular);
CREATE INDEX idx_promo_active ON promo_banners(is_active);
```

### Eager Loading
- SQLAlchemy `selectinload()` for relationships
- Prevents N+1 query problems
- Loads images, features, seller info in single query

### Pagination
- Offset-based pagination
- Configurable page size (1-100)
- Total count returned for UI pagination controls

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (validation error)
- `404 Not Found`: Resource not found (invalid game ID)
- `429 Too Many Requests`: Rate limit exceeded

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "data": null
}
```

## Testing

### Test Coverage
- `tests/test_home_feed.py`: Comprehensive endpoint tests
- Tests for success cases
- Tests for validation errors
- Tests for rate limiting
- Tests for cache functionality

### Running Tests
```bash
pytest tests/test_home_feed.py -v
```

## Future Enhancements

### Potential Improvements
1. **Elasticsearch Integration**: For advanced full-text search
2. **Recommendation Engine**: ML-based account recommendations
3. **Personalization**: User-specific feed customization
4. **Real-time Updates**: WebSocket for live listings
5. **Advanced Analytics**: Search analytics, popular queries
6. **CDN Integration**: Image optimization and caching
7. **Multi-language Support**: i18n for categories and content

### Scalability Considerations
- Database read replicas for high traffic
- Cache warming on deployment
- Background jobs for cache refresh
- Pagination cursor for large datasets

## Dependencies

### Required Packages
- `fastapi`: Web framework
- `sqlalchemy`: ORM and database toolkit
- `redis`: Caching layer
- `slowapi`: Rate limiting
- `pydantic`: Data validation

### Configuration
Add to `requirements.txt`:
```
fastapi>=0.104.0
sqlalchemy>=2.0.0
redis>=5.0.0
slowapi>=0.1.9
pydantic>=2.0.0
```

## Conclusion

The Home Feed module provides a complete discovery experience with:
- ✅ 8 public API endpoints
- ✅ Redis caching for performance
- ✅ Rate limiting for security
- ✅ Comprehensive search with filters
- ✅ Optimized database queries
- ✅ Proper error handling
- ✅ Full test coverage

The implementation follows best practices for scalability, security, and user experience.
