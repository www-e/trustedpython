# API Structure

## 🌐 API Versioning

### URL-Based Versioning (from day one)

All endpoints are versioned: `/api/v1/`, `/api/v2/`, etc.

```
# Current version
/api/v1/users
/api/v1/listings
/api/v1/deals

# Future breaking changes
/api/v2/users  # New version with different response format
```

**Rationale:**
- Clear version boundaries
- Easy deprecation paths
- Flutter app can migrate versions gradually
- Industry standard

---

## 🔐 Authentication

### JWT Token Structure

```python
# Access Token (15-minute expiration)
{
  "sub": "user_123",           # User ID
  "role": "user",              # user | mediator | admin
  "exp": 1710000000,           # Expiration timestamp
  "iat": 1709991000,           # Issued at
  "jti": "token_id_abc123"     # Unique token ID
}

# Refresh Token (7-day expiration)
{
  "sub": "user_123",
  "type": "refresh",
  "exp": 1710700000
}
```

### Authentication Flow

```
1. POST /api/v1/auth/login
   Request: { "phone": "+201234567890", "password": "secret" }
   Response: {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "token_type": "bearer",
     "expires_in": 900  # 15 minutes
   }

2. Subsequent requests
   Header: Authorization: Bearer <access_token>

3. Token expires → 401 Unauthorized
   POST /api/v1/auth/refresh
   Request: { "refresh_token": "..." }
   Response: { "access_token": "..." }

4. Logout (optional)
   POST /api/v1/auth/logout
   Adds token to blacklist (Redis)
```

### Protected Endpoints

```python
# Require authentication
@router.get("/me")
async def get_current_user(
    user: User = Depends(get_current_user)  # Auto-inject
):
    return user

# Require specific role
@router.post("/mediators")
async def create_mediator(
    data: MediatorCreate,
    admin: User = Depends(require_admin)  # Admin only
):
    return await mediator_service.create(data)

# Require any of multiple roles
@router.get("/admin/stats")
async def get_stats(
    user: User = Depends(require_roles([Role.ADMIN, Role.MEDIATOR]))
):
    return await stats_service.get()
```

---

## 📦 Response Format

### Success Responses

**Simple Object (200 OK)**
```json
{
  "id": 123,
  "title": "PUBG Account - Ace Rank",
  "price": 50,
  "status": "active"
}
```

**Array (200 OK)**
```json
{
  "items": [
    { "id": 1, "title": "Account 1" },
    { "id": 2, "title": "Account 2" }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

**Created (201 Created)**
```json
{
  "id": 456,
  "title": "New Listing",
  "created_at": "2026-03-14T10:30:00Z"
}
```

### Error Responses

**Validation Error (400 Bad Request)**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Price must be greater than 0",
  "details": {
    "field": "price",
    "value": -10,
    "constraint": "min_value"
  }
}
```

**Not Found (404 Not Found)**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Listing with ID 999 not found",
  "details": {
    "resource": "listing",
    "id": 999
  }
}
```

**Unauthorized (401 Unauthorized)**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Invalid or expired token",
  "details": null
}
```

**Forbidden (403 Forbidden)**
```json
{
  "error_code": "FORBIDDEN",
  "message": "This action requires admin privileges",
  "details": {
    "required_role": "admin",
    "user_role": "user"
  }
}
```

**Rate Limited (429 Too Many Requests)**
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Try again in 60 seconds.",
  "details": {
    "limit": 100,
    "window": 3600,
    "retry_after": 60
  }
}
```

**Server Error (500 Internal Server Error)**
```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "details": null
}
```

---

## 📚 API Endpoints

### Authentication

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
```

### Users

```
GET    /api/v1/me                              # Current user profile
PUT    /api/v1/me                              # Update profile
GET    /api/v1/users/{id}                      # Public user profile
GET    /api/v1/users/{id}/listings             # User's listings
GET    /api/v1/users/{id}/history              # User's deal history
```

### Listings

```
GET    /api/v1/listings                        # Browse listings (paginated)
POST   /api/v1/listings                        # Create listing
GET    /api/v1/listings/{id}                   # Listing details
PUT    /api/v1/listings/{id}                   # Update listing
DELETE /api/v1/listings/{id}                   # Delete listing
GET    /api/v1/listings/{id}/gallery           # Listing images
POST   /api/v1/listings/{id}/images            # Upload image
```

### Search & Filter

```
GET    /api/v1/search                          # Full-text search
GET    /api/v1/categories                     # List categories
GET    /api/v1/categories/{id}/listings        # Listings by category
```

### Deals

```
POST   /api/v1/deals                           # Request to buy (initiate deal)
GET    /api/v1/deals                           # My deals (as buyer/seller)
GET    /api/v1/deals/{id}                      # Deal details
PUT    /api/v1/deals/{id}/status               # Update deal status (Mediator only)
POST   /api/v1/deals/{id}/close                # Close deal (Mediator only)
POST   /api/v1/deals/{id}/cancel               # Cancel deal
```

### Mediators

```
GET    /api/v1/mediators                       # Mediator directory
GET    /api/v1/mediators/{id}                  # Mediator profile
GET    /api/v1/mediators/{id}/stats            # Mediator stats (success rate, etc)
GET    /api/v1/mediators/{id}/reviews          # Mediator reviews
```

### Chats

```
GET    /api/v1/chats                           # My chat rooms
GET    /api/v1/chats/{id}                      # Chat details
GET    /api/v1/chats/{id}/messages             # Chat messages (paginated)
POST   /api/v1/chats/{id}/messages             # Send message
POST   /api/v1/chats/{id}/read                 # Mark as read
POST   /api/v1/chats/{id}/proofs               # Upload proof image
```

### Notifications

```
GET    /api/v1/notifications                   # My notifications
PUT    /api/v1/notifications/{id}/read         # Mark as read
PUT    /api/v1/notifications/read-all          # Mark all as read
```

### Admin

```
GET    /api/v1/admin/users                     # All users (paginated)
GET    /api/v1/admin/users/{id}                # User details
PUT    /api/v1/admin/users/{id}/ban            # Ban user
DELETE /api/v1/admin/users/{id}/ban            # Unban user

GET    /api/v1/admin/mediators                 # All mediators
POST   /api/v1/admin/mediators                 # Create mediator
PUT    /api/v1/admin/mediators/{id}            # Update mediator
PUT    /api/v1/admin/mediators/{id}/tier       # Assign tier

GET    /api/v1/admin/listings                  # All listings
PUT    /api/v1/admin/listings/{id}/status      # Update status
DELETE /api/v1/admin/listings/{id}             # Remove listing

GET    /api/v1/admin/deals                     # All deals (monitoring)
GET    /api/v1/admin/stats                     # Platform statistics

GET    /api/v1/admin/tiers                     # All tiers
POST   /api/v1/admin/tiers                     # Create tier
PUT    /api/v1/admin/tiers/{id}                # Update tier
```

---

## 🔄 Pagination

### Cursor-Based Pagination (User-Facing)

Used for: Listings, chat messages, notifications

```
GET /api/v1/listings?limit=20&cursor=abc123

Response:
{
  "items": [...],
  "pagination": {
    "next_cursor": "xyz789",  # null if no more results
    "has_more": true,
    "limit": 20
  }
}
```

**Usage:**
```dart
// Flutter app
String cursor = null;
while (hasMore) {
  final response = await api.get('/listings?limit=20&cursor=$cursor');
  listings.addAll(response.items);
  cursor = response.pagination.next_cursor;
  hasMore = response.pagination.has_more;
}
```

### Offset-Based Pagination (Admin)

Used for: Admin dashboards, debugging

```
GET /api/v1/admin/users?page=1&per_page=20

Response:
{
  "items": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🔍 Filtering & Sorting

### Listings Filter

```
GET /api/v1/listings?game=pubg&min_price=10&max_price=100&rank=ace&verified=true&sort=newest

Query Parameters:
- game: string (pubg, freefire, etc)
- category_id: int
- min_price: decimal
- max_price: decimal
- rank: string (bronze, silver, gold, platinum, diamond, ace, conqueror)
- server: string
- verified: boolean (seller verified)
- status: enum (active, sold, archived)
- sort: enum (newest, oldest, cheapest, expensive, popular)
- search: string (full-text search)
```

### Mediators Filter

```
GET /api/v1/mediators?tier=gold&online=true&sort=highest_rated

Query Parameters:
- tier: string (bronze, silver, gold, platinum)
- online: boolean
- min_rating: decimal
- sort: enum (highest_rated, most_deals, fastest_response)
```

---

## 📤 File Upload

### Upload Flow

```
1. Request upload URL
POST /api/v1/upload/request
Request: { "file_type": "listing_image", "file_name": "screenshot.jpg" }
Response: {
  "upload_url": "https://...",
  "file_key": "listings/users/123/listing_456_abc123.jpg",
  "method": "PUT"
}

2. Upload directly to R2
PUT {upload_url}
Body: <file bytes>
Headers: Content-Type: image/jpeg, Content-Length: 12345

3. Confirm upload
POST /api/v1/upload/confirm
Request: { "file_key": "..." }
Response: { "url": "https://cdn.marketplace.com/..." }
```

### Supported File Types

- **Listing images**: JPG, PNG, WEBP (max 5MB)
- **Avatars**: JPG, PNG (max 2MB)
- **Proof images**: JPG, PNG, PDF (max 10MB)

---

## 🔒 Rate Limiting

### Rate Limits by Endpoint

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| Authentication | 5 requests | 1 minute |
| Listing creation | 10 requests | 1 hour |
| Chat messages | 60 requests | 1 minute |
| Search/browse | 100 requests | 1 minute |
| Admin endpoints | 1000 requests | 1 hour |

### Response Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710000000
```

### Error Response

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "details": {
    "limit": 100,
    "window": 60,
    "retry_after": 45
  }
}
```

---

## 🌍 CORS Configuration

### Development (.env.dev)
```
CORS_ORIGINS=*
```

### Production (.env.prod)
```
CORS_ORIGINS=https://marketplace.com,https://www.marketplace.com
```

---

## 📖 API Documentation

### Interactive Docs

- **Swagger UI**: `https://api.marketplace.com/docs`
- **ReDoc**: `https://api.marketplace.com/redoc`

### OpenAPI Spec

Auto-generated from Pydantic models at `/api/v1/openapi.json`

---

## 🧪 API Testing

### Using cURL

```bash
# Login
curl -X POST https://api.marketplace.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"+201234567890","password":"secret"}'

# Create listing
curl -X POST https://api.marketplace.com/api/v1/listings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"PUBG Account","price":50,"category_id":1}'

# Get listings
curl https://api.marketplace.com/api/v1/listings?limit=20
```

### Using Swagger UI

1. Navigate to `/docs`
2. Click "Authorize" → Enter JWT token
3. Try endpoints interactively
4. View request/response examples

---

## 📚 Related Documentation

- [Architecture Design](../02-Architecture-Design.md) - How API fits into architecture
- [Realtime Architecture](../architecture/Realtime-Architecture.md) - WebSocket API
- [Development Workflow](../workflow/Development-Workflow.md) - How to develop APIs

---

**Last Updated**: 2026-03-14
**Version**: 0.1.0
