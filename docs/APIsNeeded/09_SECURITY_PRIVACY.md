# 09 - Security & Privacy APIs

> **Priority:** P1 (High - User Trust)  
> **Base Path:** `/api/v1/security`  
> **Status:** ✅ COMPLETE  
> **UI Analysis:** Complete understanding of security screen, 2FA, biometric, password change

---

## Overview

Security & Privacy settings allow users to manage their account security including:
- **Password Management** - Change password
- **Two-Factor Authentication (2FA)** - Enable/disable
- **Biometric Authentication** - Fingerprint/Face ID
- **Login Notifications** - Alerts for new logins
- **Email Verification** - Verify email status
- **Active Sessions** - View/manage active sessions

---

## API Endpoints Overview

| # | Endpoint | Method | Auth | Description |
|---|----------|--------|------|-------------|
| 1 | `/security/settings` | GET | Yes | Get security settings |
| 2 | `/security/change-password` | POST | Yes | Change password |
| 3 | `/security/two-factor/enable` | POST | Yes | Enable 2FA |
| 4 | `/security/two-factor/disable` | POST | Yes | Disable 2FA |
| 5 | `/security/two-factor/verify` | POST | Yes | Verify 2FA code |
| 6 | `/security/biometric/enable` | POST | Yes | Enable biometric |
| 7 | `/security/biometric/disable` | POST | Yes | Disable biometric |
| 8 | `/security/login-notifications` | PUT | Yes | Toggle login notifications |
| 9 | `/security/sessions` | GET | Yes | Get active sessions |
| 10 | `/security/sessions/{sessionId}` | DELETE | Yes | Revoke session |
| 11 | `/security/login-history` | GET | Yes | Get login history |

---

## 1. Get Security Settings

### `GET /api/v1/security/settings`

Get user's current security settings.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "two_factor_enabled": "boolean",
    "biometric_enabled": "boolean",
    "login_notifications_enabled": "boolean",
    "last_password_change": "ISO 8601 date",
    "email_verified": "boolean",
    "phone_verified": "boolean"
  }
}
```

---

## 2. Change Password

### `POST /api/v1/security/change-password`

Change user password.

#### Request
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, 6+ chars)",
  "confirm_password": "string (required, must match new_password)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "message": "Password changed successfully",
  "data": {
    "last_password_change": "ISO 8601 date"
  }
}
```

#### Error Responses
- **400 Bad Request** - Passwords don't match
- **400 Bad Request** - New password too short
- **401 Unauthorized** - Current password incorrect
- **403 Forbidden** - Account requires password reset

---

## 3. Enable Two-Factor Authentication

### `POST /api/v1/security/two-factor/enable`

Enable 2FA for the account.

#### Request
```json
{
  "password": "string (required)",
  "code": "string (6-digit TOTP code, required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "two_factor_enabled": true,
    "backup_codes": ["string (10 single-use codes)"],
    "qr_code_url": "string (for authenticator app)"
  }
}
```

#### Error Responses
- **400 Bad Request** - Invalid 2FA code
- **401 Unauthorized** - Password incorrect

---

## 4. Disable Two-Factor Authentication

### `POST /api/v1/security/two-factor/disable`

Disable 2FA.

#### Request
```json
{
  "password": "string (required)",
  "code": "string (6-digit TOTP code, required)"
}
```

---

## 5. Verify Two-Factor Code

### `POST /api/v1/security/two-factor/verify`

Verify a 2FA code (used during login).

#### Request
```json
{
  "code": "string (6-digit TOTP code, required)",
  "user_id": "string (required)"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 3600
  }
}
```

---

## 6. Enable Biometric Authentication

### `POST /api/v1/security/biometric/enable`

Enable biometric login (fingerprint/face ID).

#### Success Response (200)
```json
{
  "success": true,
  "message": "Biometric authentication enabled"
}
```

**Note:** Biometric auth is primarily client-side. The backend just stores the preference.

---

## 7. Disable Biometric Authentication

### `POST /api/v1/security/biometric/disable`

Disable biometric login.

---

## 8. Toggle Login Notifications

### `PUT /api/v1/security/login-notifications`

Enable/disable login notifications.

#### Request
```json
{
  "enabled": "boolean (required)"
}
```

---

## 9. Get Active Sessions

### `GET /api/v1/security/sessions`

Get all active sessions for the user.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "string (UUID)",
        "device_info": {
          "device": "string (e.g., iPhone 15 Pro)",
          "os": "string (e.g., iOS 17.2)",
          "browser": "string | null",
          "app_version": "string | null"
        },
        "ip_address": "string",
        "location": {
          "city": "string | null",
          "country": "string | null"
        },
        "last_active_at": "ISO 8601 datetime",
        "created_at": "ISO 8601 datetime",
        "is_current": "boolean"
      }
    ]
  }
}
```

---

## 10. Revoke Session

### `DELETE /api/v1/security/sessions/{sessionId}`

Revoke an active session (logout from that device).

#### Success Response (200)
```json
{
  "success": true,
  "message": "Session revoked successfully"
}
```

---

## 11. Get Login History

### `GET /api/v1/security/login-history?page={page}&limit={limit}`

Get historical login attempts.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "logins": [
      {
        "id": "string",
        "timestamp": "ISO 8601 datetime",
        "status": "success | failed",
        "failure_reason": "string | null",
        "device_info": {
          "device": "string",
          "os": "string"
        },
        "ip_address": "string",
        "location": {
          "city": "string | null",
          "country": "string | null"
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

## 2FA Flow Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                  2FA ENABLEMENT FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. User requests 2FA enablement
2. Backend generates secret key & QR code
3. User scans QR code with authenticator app
4. User enters 6-digit code from app
5. Backend verifies code
6. Backend saves 2FA status + backup codes
7. Returns backup codes to user (one-time display)

┌─────────────────────────────────────────────────────────────┐
│                  2FA LOGIN FLOW                             │
└─────────────────────────────────────────────────────────────┘

1. User enters username/password
2. Backend validates credentials
3. If 2FA enabled, returns "2fa_required": true
4. User enters 6-digit code
5. Backend verifies code
6. Returns access/refresh tokens
```

---

## Security Requirements

- ✅ All security endpoints require authentication
- ✅ Password change requires current password verification
- ✅ 2FA codes are time-based (TOTP, 30-second windows)
- ✅ Backup codes are single-use, hashed in database
- ✅ Login notifications sent via push + email
- ✅ Session revocation invalidates tokens immediately
- ✅ Brute force protection on password change (max 5 attempts/hour)
- ✅ Audit log for all security-sensitive operations
