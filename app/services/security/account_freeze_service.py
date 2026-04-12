"""
Account freeze management service.

Handles account freezing and unfreezing for security reasons.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.schemas.security import SuccessResponse
from app.services.security.base import log_security_event
from app.services.security.password_service import PasswordService


class AccountFreezeService:
    """
    Service for account freeze operations.

    Provides methods for freezing and unfreezing user accounts.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize account freeze service.

        Args:
            db: Database session
        """
        self.db = db

    async def freeze_account(
        self, user_id: UUID, reason: str, duration_hours: int
    ) -> SuccessResponse:
        """
        Freeze user account for security reasons.

        Args:
            user_id: ID of the user
            reason: Reason for freezing
            duration_hours: Duration in hours

        Returns:
            SuccessResponse with freeze confirmation

        Raises:
            NotFoundError: If user not found
            ValidationError: If account already frozen
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if user.is_frozen:
            raise ValidationError("Account is already frozen")

        # Calculate unfreeze time
        unfreeze_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        # Freeze account
        user.is_frozen = True
        user.frozen_until = unfreeze_at
        user.freeze_reason = reason

        await self.db.commit()
        await self.db.refresh(user)

        # Logout all sessions
        password_service = PasswordService(self.db)
        await password_service.logout_all_sessions(user_id)

        # Log security event
        await log_security_event(
            self.db,
            user_id,
            "account_frozen",
            {
                "reason": reason,
                "duration_hours": duration_hours,
                "unfreeze_at": unfreeze_at.isoformat(),
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Account frozen successfully. Will be automatically unfrozen on {unfreeze_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        )

    async def unfreeze_account(self, user_id: UUID) -> SuccessResponse:
        """
        Unfreeze user account.

        Args:
            user_id: ID of the user

        Returns:
            SuccessResponse with unfreeze confirmation

        Raises:
            NotFoundError: If user not found
            ValidationError: If account not frozen
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        if not user.is_frozen:
            raise ValidationError("Account is not frozen")

        # Unfreeze account
        user.is_frozen = False
        user.frozen_until = None
        user.freeze_reason = None

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await log_security_event(
            self.db,
            user_id,
            "account_unfrozen",
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        return SuccessResponse(success=True, message="Account unfrozen successfully")
