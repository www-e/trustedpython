"""
Login history and session management service.

Handles login history tracking and security settings management.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import LoginHistory, Session, TrustedDevice, User
from app.schemas.security import (
    LoginHistoryItem,
    LoginHistoryResponse,
    SecuritySettingsResponse,
    UpdateSecuritySettingsRequest,
)
from app.core.security import hash_password
from app.services.security.base import get_active_sessions_count, log_security_event


class LoginHistoryService:
    """
    Service for login history and security settings operations.

    Provides methods for tracking login history and managing security settings.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize login history service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_login_history(
        self, user_id: UUID, page: int = 1, page_size: int = 20, status_filter: Optional[str] = None
    ) -> LoginHistoryResponse:
        """
        Get user's login history with pagination.

        Args:
            user_id: ID of the user
            page: Page number
            page_size: Items per page
            status_filter: Optional status filter

        Returns:
            LoginHistoryResponse with paginated history
        """
        # Build query
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)

        if status_filter:
            query = query.where(LoginHistory.status == status_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(LoginHistory.timestamp))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        history_items = result.scalars().all()

        # Convert to response format
        history = [
            LoginHistoryItem(
                timestamp=item.timestamp,
                ip_address=item.ip_address,
                device_info=item.device_info,
                status=item.status,
                location=item.location,
            )
            for item in history_items
        ]

        return LoginHistoryResponse(total=total, page=page, page_size=page_size, history=history)

    async def get_security_settings(self, user_id: UUID) -> SecuritySettingsResponse:
        """
        Get user's security settings.

        Args:
            user_id: ID of the user

        Returns:
            SecuritySettingsResponse with user's security settings

        Raises:
            NotFoundError: If user not found
        """
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Get trusted devices
        trusted_devices_result = await self.db.execute(
            select(TrustedDevice).where(
                and_(TrustedDevice.user_id == user_id, TrustedDevice.is_active == True)
            )
        )
        trusted_devices = trusted_devices_result.scalars().all()

        trusted_devices_list = [
            {
                "id": str(device.id),
                "device_name": device.device_name,
                "device_info": device.device_info,
                "last_used": device.last_used.isoformat() if device.last_used else None,
                "created_at": device.created_at.isoformat(),
            }
            for device in trusted_devices
        ]

        # Get active sessions count
        active_sessions = await get_active_sessions_count(self.db, user_id)

        return SecuritySettingsResponse(
            two_factor_enabled=user.two_factor_enabled or False,
            login_notifications=user.login_notifications or False,
            trusted_devices=trusted_devices_list,
            security_questions=user.security_questions or {},
            last_password_change=user.password_changed_at,
            active_sessions=active_sessions,
        )

    async def update_security_settings(
        self, user_id: UUID, data: UpdateSecuritySettingsRequest
    ) -> SecuritySettingsResponse:
        """
        Update user's security settings.

        Args:
            user_id: ID of the user
            data: Security settings update data

        Returns:
            SecuritySettingsResponse with updated settings

        Raises:
            NotFoundError: If user not found
        """
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Update settings
        if data.login_notifications is not None:
            user.login_notifications = data.login_notifications

        if data.security_questions is not None:
            # Hash security question answers
            hashed_questions = {
                k: hash_password(v) if v else None for k, v in data.security_questions.items()
            }
            user.security_questions = {**(user.security_questions or {}), **hashed_questions}

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await log_security_event(
            self.db,
            user_id,
            "security_settings_updated",
            {
                "login_notifications": data.login_notifications,
                "security_questions_updated": bool(data.security_questions),
            },
        )

        return await self.get_security_settings(user_id)
