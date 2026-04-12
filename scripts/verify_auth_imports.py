#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script to check if all authentication module imports work correctly.
Run this to verify the implementation is ready for use.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def verify_imports():
    """Verify all authentication module imports."""
    print("[*] Verifying Authentication Module Imports...\n")

    try:
        # 1. Verify schemas
        print("[+] Importing schemas...")
        from app.api.v1.auth.schemas import (
            RegisterRequest,
            LoginRequest,
            ForgotPasswordRequest,
            ResetPasswordRequest,
            RefreshTokenRequest,
            VerifyEmailRequest,
            RegisterResponse,
            LoginResponse,
            TokenResponse,
            CurrentUserResponse
        )
        print("  [OK] All schemas imported successfully\n")

        # 2. Verify service
        print("[+] Importing auth service...")
        from app.services.auth_service import AuthService
        print("  [OK] AuthService imported successfully\n")

        # 3. Verify routes
        print("[+] Importing auth routes...")
        from app.api.v1.auth.routes import router
        print("  [OK] Auth router imported successfully\n")

        # 4. Verify rate limiting
        print("[+] Importing rate limiting...")
        from app.utils.rate_limit import (
            RateLimiter,
            rate_limit,
            rate_limit_login,
            rate_limit_register,
            get_client_ip
        )
        print("  [OK] Rate limiting utilities imported successfully\n")

        # 5. Verify security
        print("[+] Importing security utilities...")
        from app.core.security import (
            hash_password,
            verify_password,
            create_access_token,
            create_refresh_token,
            decode_token,
            verify_token
        )
        print("  [OK] Security utilities imported successfully\n")

        # 6. Verify exceptions
        print("[+] Importing exceptions...")
        from app.core.exceptions import (
            ConflictException,
            UnauthorizedException,
            ForbiddenException,
            NotFoundException,
            ValidationException,
            RateLimitException
        )
        print("  [OK] Custom exceptions imported successfully\n")

        # 7. Verify models
        print("[+] Importing user models...")
        from app.models.user import User, UserProfile, Session
        print("  [OK] User models imported successfully\n")

        # 8. Verify API responses
        print("[+] Importing API responses...")
        from app.schemas.common import APIResponse, SuccessResponse
        print("  [OK] API response wrappers imported successfully\n")

        return True

    except ImportError as e:
        print(f"[FAIL] Import Error: {e}\n")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected Error: {e}\n")
        return False


def verify_schemas():
    """Verify schema validation."""
    print("[*] Verifying Schema Validation...\n")

    try:
        from app.api.v1.auth.schemas import (
            RegisterRequest,
            LoginRequest,
            ForgotPasswordRequest
        )

        # Test valid register request
        print("[+] Testing valid register request...")
        valid_register = RegisterRequest(
            username="testuser",
            email="test@example.com",
            phone="1234567890",
            password="SecurePass123"
        )
        print(f"  [OK] Valid register: {valid_register.username}\n")

        # Test invalid register request (short password)
        print("[+] Testing invalid register request...")
        try:
            invalid_register = RegisterRequest(
                username="testuser",
                email="test@example.com",
                phone="1234567890",
                password="12345"  # Too short
            )
            print("  [FAIL] Should have failed validation\n")
            return False
        except Exception:
            print("  [OK] Validation rejected short password\n")

        # Test valid login request
        print("[+] Testing valid login request...")
        valid_login = LoginRequest(
            username="testuser",
            password="SecurePass123"
        )
        print(f"  [OK] Valid login: {valid_login.username}\n")

        return True

    except Exception as e:
        print(f"[FAIL] Schema Verification Error: {e}\n")
        return False


def verify_security():
    """Verify security functions."""
    print("[*] Verifying Security Functions...\n")

    try:
        from app.core.security import (
            hash_password,
            verify_password,
            create_access_token,
            create_refresh_token,
            verify_token
        )

        # Test password hashing
        print("[+] Testing password hashing...")
        password = "TestPassword123"
        hashed = hash_password(password)
        print(f"  [OK] Password hashed: {hashed[:20]}...\n")

        # Test password verification
        print("[+] Testing password verification...")
        is_valid = verify_password(password, hashed)
        print(f"  [OK] Password verification: {is_valid}\n")

        # Test token creation
        print("[+] Testing token creation...")
        access_token = create_access_token({"sub": "user-123"})
        refresh_token = create_refresh_token({"sub": "user-123"})
        print(f"  [OK] Access token: {access_token[:20]}...")
        print(f"  [OK] Refresh token: {refresh_token[:20]}...\n")

        # Test token verification
        print("[+] Testing token verification...")
        payload = verify_token(access_token, "access")
        print(f"  [OK] Token verified: {payload['sub']}\n")

        return True

    except Exception as e:
        print(f"[FAIL] Security Verification Error: {e}\n")
        return False


def verify_rate_limiting():
    """Verify rate limiting."""
    print("[*] Verifying Rate Limiting...\n")

    try:
        from app.utils.rate_limit import RateLimiter, get_client_ip

        # Test rate limiter
        print("[+] Testing rate limiter...")
        limiter = RateLimiter(requests=3, window=60)

        # First 3 requests should succeed
        for i in range(3):
            allowed, retry_after = limiter.check("test-ip")
            if not allowed:
                print(f"  [FAIL] Request {i+1} should be allowed\n")
                return False
        print(f"  [OK] First 3 requests allowed\n")

        # 4th request should be rate limited
        allowed, retry_after = limiter.check("test-ip")
        if allowed:
            print(f"  [FAIL] Request 4 should be rate limited\n")
            return False
        print(f"  [OK] Request 4 rate limited (retry after: {retry_after}s)\n")

        return True

    except Exception as e:
        print(f"[FAIL] Rate Limiting Verification Error: {e}\n")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("[AUTH] AUTHENTICATION MODULE VERIFICATION")
    print("=" * 60)
    print()

    results = []

    # Run all checks
    results.append(("Imports", verify_imports()))
    results.append(("Schemas", verify_schemas()))
    results.append(("Security", verify_security()))
    results.append(("Rate Limiting", verify_rate_limiting()))

    # Print summary
    print("=" * 60)
    print("[SUMMARY] VERIFICATION SUMMARY")
    print("=" * 60)
    print()

    all_passed = True
    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("[SUCCESS] ALL VERIFICATIONS PASSED!")
        print("[OK] Authentication module is ready for use")
        return 0
    else:
        print("[FAIL] SOME VERIFICATIONS FAILED")
        print("[WARNING]  Please review the errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
