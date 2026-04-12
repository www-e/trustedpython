# Authentication API - Quick Reference

## Base URL
```
http://localhost:8000/api/v1/auth
```

---

## Endpoints

### 1. Register User
```http
POST /auth/register
```

**Request Body:**
```json
{
  "username": "gamer123",
  "email": "user@example.com",
  "phone": "1234567890",
  "password": "SecurePass123"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": {
      "id": "uuid",
      "username": "gamer123",
      "email": "user@example.com",
      "phone": "1234567890",
      "display_name": "gamer123",
      "created_at": "2025-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

**Errors:**
- `400` - Validation error
- `409` - Username/email/phone already exists
- `429` - Rate limit exceeded (3 per minute)

---

### 2. Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "username": "gamer123",
  "password": "SecurePass123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "gamer123",
      "email": "user@example.com",
      "display_name": "gamer123",
      "created_at": "2025-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Account suspended/deactivated
- `429` - Rate limit exceeded (5 per minute)

---

### 3. Forgot Password
```http
POST /auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset link sent to your email"
}
```

**Errors:**
- `404` - Email not registered

---

### 4. Reset Password
```http
POST /auth/reset-password
```

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Errors:**
- `400` - Invalid/expired token
- `400` - Password too short

---

### 5. Refresh Token
```http
POST /auth/refresh-token
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "new_access_token",
    "refresh_token": "new_refresh_token",
    "expires_in": 3600
  }
}
```

**Errors:**
- `401` - Invalid refresh token

---

### 6. Logout
```http
POST /auth/logout
```

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Errors:**
- `401` - Not authenticated

---

### 7. Get Current User
```http
GET /auth/me
```

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "gamer123",
    "email": "user@example.com",
    "phone": "1234567890",
    "display_name": "Gamer123",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_verified": false,
    "created_at": "2025-01-01T00:00:00Z",
    "stats": {
      "total_sales": 5,
      "total_purchases": 2,
      "rating": 4.5,
      "reviews_count": 10
    }
  }
}
```

**Errors:**
- `401` - Not authenticated

---

### 8. Verify Email
```http
POST /auth/verify-email
```

**Request Body:**
```json
{
  "token": "verification_token_from_email"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Email verified successfully"
}
```

**Errors:**
- `400` - Invalid/expired token

---

## Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "status_code": 400
}
```

### Common Error Codes:
- `VALIDATION_ERROR` - Invalid input
- `UNAUTHORIZED` - Not authenticated
- `FORBIDDEN` - Account suspended
- `NOT_FOUND` - Resource not found
- `CONFLICT` - Duplicate resource
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/register | 3 | 1 minute |
| POST /auth/login | 5 | 1 minute |
| Other endpoints | 100 | 1 minute |

**Rate Limit Response:**
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again in 30 seconds",
  "retry_after": 30
}
```

---

## Token Usage

### Access Token:
- **Expiration**: 1 hour
- **Usage**: API requests (Authorization header)
- **Format**: `Bearer ACCESS_TOKEN`

### Refresh Token:
- **Expiration**: 7 days
- **Usage**: Get new access token
- **Storage**: Secure storage (e.g., AsyncStorage/Keychain)

---

## Authentication Flow

```
1. REGISTER
   Client → POST /auth/register → Server
   Client ← {user, tokens} ← Server

2. LOGIN
   Client → POST /auth/login → Server
   Client ← {user, tokens} ← Server

3. USE TOKEN
   Client → GET /auth/me (with token) → Server
   Client ← {user profile} ← Server

4. REFRESH (when expired)
   Client → POST /auth/refresh-token → Server
   Client ← {new tokens} ← Server

5. LOGOUT
   Client → POST /auth/logout (with token) → Server
   Client ← {success} ← Server
```

---

## Testing with cURL

### Register:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "phone": "1234567890",
    "password": "TestPass123"
  }'
```

### Login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'
```

### Get Current User:
```bash
TOKEN="your_access_token_here"
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token:
```bash
REFRESH="your_refresh_token_here"
curl -X POST http://localhost:8000/api/v1/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}"
```

### Logout:
```bash
TOKEN="your_access_token_here"
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

## Validation Rules

### Username:
- Min length: 3 characters
- Max length: 50 characters
- Pattern: Alphanumeric + underscore only
- Example: `gamer123`, `test_user`

### Email:
- Must be valid email format
- Example: `user@example.com`

### Phone:
- Min length: 10 digits
- Pattern: Numbers only
- Example: `1234567890`

### Password:
- Min length: 6 characters
- Max length: 100 characters
- Example: `SecurePass123`

---

## Security Features

✅ **Password Hashing**: Bcrypt with salt
✅ **JWT Tokens**: HS256 algorithm
✅ **Token Expiration**: Access (1h), Refresh (7d)
✅ **Rate Limiting**: Prevents brute force
✅ **Account Suspension**: Reason tracking
✅ **Email Verification**: Required for full access
✅ **Password Reset**: Secure token flow

---

## Next Steps

1. **Integration Testing**: Test with frontend
2. **Email Service**: Implement email templates
3. **Token Blacklist**: Add Redis for logout
4. **Session Management**: Track active sessions
5. **OAuth2**: Add social login (Google, Apple)
6. **2FA**: Add two-factor authentication
