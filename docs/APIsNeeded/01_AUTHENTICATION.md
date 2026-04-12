# 01 - Authentication APIs

> **Priority:** P0 (Critical - Foundation)  
> **Base Path:** `/api/v1/auth`  
> **Status:** Ready for implementation  
> **UI Analysis:** Complete understanding of login, signup, forgot password flows

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/auth/register` | POST | No | User registration |
| 2 | `/auth/login` | POST | No | User authentication |
| 3 | `/auth/forgot-password` | POST | No | Request password reset |
| 4 | `/auth/reset-password` | POST | No | Reset password with token |
| 5 | `/auth/refresh-token` | POST | No | Refresh access token |
| 6 | `/auth/logout` | POST | Yes | User logout |
| 7 | `/auth/me` | GET | Yes | Get current user profile |
| 8 | `/auth/verify-email` | POST | No | Verify email address |

---

## 1. Register User

### `POST /api/v1/auth/register`

Register a new user account.

#### Request
```json
{
  "username": "string (3+ chars, required)",
  "phone": "string (10+ digits, required)",
  "email": "string (valid email, required)",
  "password": "string (6+ chars, required)"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": {
      "id": "string (UUID)",
      "username": "string",
      "email": "string",
      "phone": "string",
      "display_name": "string | null",
      "created_at": "ISO 8601 datetime"
    },
    "access_token": "JWT token string",
    "refresh_token": "JWT refresh token string",
    "expires_in": 3600
  }
}
```

#### Error Responses
- **400 Bad Request** - Validation errors
- **409 Conflict** - Username/email/phone already exists

---

## 2. Login

### `POST /api/v1/auth/login`

Authenticate user and return tokens.

#### Request
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "string",
      "username": "string",
      "email": "string | null",
      "display_name": "string | null",
      "created_at": "ISO 8601 datetime"
    },
    "access_token": "JWT token",
    "refresh_token": "JWT refresh token",
    "expires_in": 3600
  }
}
```

#### Error Responses
- **401 Unauthorized** - Invalid credentials
- **403 Forbidden** - Account suspended/deactivated

---

## 3. Forgot Password

### `POST /api/v1/auth/forgot-password`

Send password reset link to email.

#### Request
```json
{
  "email": "string (valid email, required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Password reset link sent to your email"
}
```

#### Error Responses
- **404 Not Found** - Email not registered

---

## 4. Reset Password

### `POST /api/v1/auth/reset-password`

Reset password using token from email.

#### Request
```json
{
  "token": "string (from email, required)",
  "new_password": "string (6+ chars, required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

#### Error Responses
- **400 Bad Request** - Invalid/expired token
- **400 Bad Request** - Password too short

---

## 5. Refresh Token

### `POST /api/v1/auth/refresh-token`

Get new access token using refresh token.

#### Request
```json
{
  "refresh_token": "string (required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "access_token": "new JWT token",
    "refresh_token": "new refresh token",
    "expires_in": 3600
  }
}
```

---

## 6. Logout

### `POST /api/v1/auth/logout`

Invalidate user session.

#### Headers
```
Authorization: Bearer {access_token}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 7. Get Current User

### `GET /api/v1/auth/me`

Get authenticated user profile.

#### Headers
```
Authorization: Bearer {access_token}
```

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
    "created_at": "ISO 8601 datetime",
    "stats": {
      "total_sales": "number",
      "total_purchases": "number",
      "rating": "number (0-5)",
      "reviews_count": "number"
    }
  }
}
```

---

## 8. Verify Email

### `POST /api/v1/auth/verify-email`

Verify user email address.

#### Request
```json
{
  "token": "string (from verification email, required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Email verified successfully"
}
```

---

## Authentication Flow Sequence

```
┌─────────┐         ┌──────────┐         ┌───────────┐
│  Client │         │   API    │         │  Backend  │
└────┬────┘         └────┬─────┘         └─────┬─────┘
     │                   │                     │
     │  POST /login      │                     │
     ├──────────────────►│                     │
     │                   │  Validate creds     │
     │                   ├────────────────────►│
     │                   │                     │
     │                   │  Generate tokens    │
     │                   │◄────────────────────┤
     │                   │                     │
     │  {user, tokens}   │                     │
     │◄──────────────────┤                     │
     │                   │                     │
     │  Store tokens     │                     │
     │  locally          │                     │
     │                   │                     │
     │  POST /refresh    │                     │
     │  (when expired)   │                     │
     ├──────────────────►│                     │
     │                   │  Validate refresh   │
     │                   ├────────────────────►│
     │                   │                     │
     │                   │  New tokens         │
     │                   │◄────────────────────┤
     │  {new tokens}     │                     │
     │◄──────────────────┤                     │
     │                   │                     │
     │  POST /logout     │                     │
     ├──────────────────►│  Invalidate tokens  │
     │                   ├────────────────────►│
     │  Clear local      │                     │
     │  storage          │                     │
     │◄──────────────────┤                     │
```

---

## Security Requirements

- ✅ All endpoints must use HTTPS
- ✅ Password hashing: bcrypt or argon2
- ✅ JWT tokens with reasonable expiry (access: 1h, refresh: 30d)
- ✅ Rate limiting on login/register (prevent brute force)
- ✅ Email verification required for full account access
- ✅ Password reset tokens expire after 1 hour
- ✅ Input sanitization on all fields
- ✅ CORS configured for Flutter app domains
