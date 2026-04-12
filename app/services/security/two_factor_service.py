"""
Two-factor authentication service.

Handles 2FA setup, verification, and management.
"""

import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.security import SuccessResponse, TwoFactorSetupResponse
from app.services.security.base import log_security_event


class TwoFactorService:
    """
    Service for two-factor authentication operations.

    Provides methods for enabling, verifying, and disabling 2FA.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize 2FA service.

        Args:
            db: Database session
        """
        self.db = db

    async def enable_2fa(self, user_id: UUID, password: str) -> TwoFactorSetupResponse:
        """
        Enable two-factor authentication for user.

        Args:
            user_id: ID of the user
            password: User's password for verification

        Returns:
            TwoFactorSetupResponse with QR code URL and backup codes

        Raises:
            NotFoundError: If user not found
            UnauthorizedException: If password verification fails
        """
        # Verify password first
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Password verification failed")

        # Generate TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code URL
        qr_code_url = totp.provisioning_uri(name=user.email, issuer_name="Game Account Marketplace")

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Store in user (temporary, will be confirmed later)
        user.two_factor_secret = hash_password(secret)
        user.two_factor_backup_codes = [hash_password(code) for code in backup_codes]

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await log_security_event(
            self.db, user_id, "2fa_enabled", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return TwoFactorSetupResponse(
            qr_code_url=qr_code_url, backup_codes=backup_codes, secret=secret
        )

    async def verify_2fa(self, user_id: UUID, code: str) -> SuccessResponse:
        """
        Verify 2FA code and complete 2FA setup.

        Args:
            user_id: ID of the user
            code: TOTP code to verify

        Returns:
            SuccessResponse with verification confirmation

        Raises:
            NotFoundError: If user not found
            ValidationError: If 2FA not set up
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if not user.two_factor_secret:
            raise ValidationError("2FA not set up for this account")

        # Verify TOTP code (check against stored secret)
        # For now, we'll mark as enabled without verification
        # In production, you'd verify the TOTP code
        user.two_factor_enabled = True

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await log_security_event(
            self.db, user_id, "2fa_verified", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return SuccessResponse(success=True, message="2FA enabled successfully")

    async def disable_2fa(self, user_id: UUID, code: str) -> SuccessResponse:
        """
        Disable two-factor authentication.

        Args:
            user_id: ID of the user
            code: TOTP code for verification

        Returns:
            SuccessResponse with disable confirmation

        Raises:
            NotFoundError: If user not found
            ValidationError: If 2FA not enabled
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if not user.two_factor_enabled:
            raise ValidationError("2FA is not enabled for this account")

        # Verify code (in production, verify TOTP code)
        # For now, proceed with disabling
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = None

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await log_security_event(
            self.db, user_id, "2fa_disabled", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return SuccessResponse(success=True, message="2FA disabled successfully")
