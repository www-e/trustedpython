"""
Password management service.

Handles password changes and session management operations.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.user import Session, User
from app.schemas.security import ChangePasswordRequest, ChangePasswordResponse, SuccessResponse
from app.services.security.base import log_security_event


class PasswordService:
    """
    Service for password management operations.

    Provides methods for changing passwords and managing user sessions.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize password service.

        Args:
            db: Database session
        """
        self.db = db

    async def change_password(
        self, user_id: UUID, data: ChangePasswordRequest
    ) -> ChangePasswordResponse:
        """
        Change user password with current password verification.

        Args:
            user_id: ID of the user
            data: Password change request data

        Returns:
            ChangePasswordResponse with success status

        Raises:
            NotFoundError: If user not found
            UnauthorizedException: If current password is incorrect
            ValidationError: If new password is same as current
        """
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            # Log failed attempt
            await log_security_event(
                self.db, user_id, "password_change_failed", {"reason": "incorrect_current_password"}
            )
            raise UnauthorizedException("Current password is incorrect")

        # Check new password is not same as current
        if verify_password(data.new_password, user.password_hash):
            raise ValidationError("New password must be different from current password")

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.requires_password_change = False

        await self.db.commit()
        await self.db.refresh(user)

        # Log successful password change
        await log_security_event(
            self.db,
            user_id,
            "password_changed",
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        return ChangePasswordResponse(success=True, message="Password changed successfully")

    async def logout_all_sessions(self, user_id: UUID) -> SuccessResponse:
        """
        Logout user from all sessions by invalidating all refresh tokens.

        Args:
            user_id: ID of the user

        Returns:
            SuccessResponse with logout confirmation
        """
        # Delete all refresh tokens for user
        await self.db.execute(delete(Session).where(Session.user_id == user_id))

        await self.db.commit()

        # Log security event
        await log_security_event(
            self.db,
            user_id,
            "all_sessions_terminated",
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        return SuccessResponse(success=True, message="Logged out from all devices successfully")
