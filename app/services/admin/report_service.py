"""
Report service for managing user reports and blocked users.

Handles report viewing, resolution, and user blocking/unblocking functionality.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.user import User, UserProfile
from app.schemas.admin import BlockedUserItem, BlockedUsersResponse, ReportsResponse


class ReportService:
    """
    Service for managing user reports and blocked users.

    Provides functionality for viewing reports, resolving them,
    and managing blocked/banned users.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize ReportService.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_reports(
        self,
        status: Optional[str] = None,
        type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> ReportsResponse:
        """
        Get user reports.

        Args:
            status: Filter by status (pending, resolved, dismissed)
            type: Filter by type (user, listing, message, deal)
            page: Page number
            limit: Items per page

        Returns:
            ReportsResponse: List of reports

        Note:
            This is a placeholder implementation. In production, you would
            need a Report model to store user reports.
        """
        # Placeholder implementation
        # In production, query from a Report model
        return ReportsResponse(reports=[], pagination={"page": page, "limit": limit, "total": 0})

    async def get_report_details(self, report_id: UUID) -> Dict[str, Any]:
        """
        Get report details.

        Args:
            report_id: Report ID

        Returns:
            Report details

        Raises:
            NotFoundException: If report not found

        Note:
            This is a placeholder implementation. In production, you would
            need a Report model to store user reports.
        """
        # Placeholder implementation
        raise NotFoundException(str(report_id), "Report")

    async def resolve_report(self, report_id: UUID, action: str, notes: str) -> Dict[str, Any]:
        """
        Resolve a report.

        Args:
            report_id: Report ID
            action: Action taken (none, warning, suspend, ban, remove_content)
            notes: Resolution notes

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If report not found

        Note:
            This is a placeholder implementation. In production, you would
            need a Report model to store user reports.
        """
        # Placeholder implementation
        await self._log_admin_action(
            "resolve_report", report_id, f"Action: {action}, Notes: {notes}"
        )
        return {"message": "Report resolved successfully"}

    async def get_blocked_users(self, page: int = 1, limit: int = 20) -> BlockedUsersResponse:
        """
        Get blocked/banned users.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            BlockedUsersResponse: List of blocked users
        """
        # Get suspended users
        result = await self.db.execute(
            select(User)
            .join(UserProfile)
            .where(User.is_suspended == True)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        users = result.scalars().all()

        # Get total count
        total = await self.db.scalar(select(func.count(User.id)).where(User.is_suspended == True))

        # Transform to response format
        user_items = []
        for user in users:
            block_type = "banned" if "BANNED" in (user.suspension_reason or "") else "suspended"
            user_items.append(
                BlockedUserItem(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    display_name=user.profile.display_name if user.profile else None,
                    avatar_url=user.profile.avatar_url if user.profile else None,
                    block_reason=user.suspension_reason or "No reason provided",
                    blocked_at=user.updated_at,
                    block_type=block_type,
                )
            )

        return BlockedUsersResponse(
            users=user_items, pagination={"page": page, "limit": limit, "total": total or 0}
        )

    async def unblock_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Unblock a user.

        Args:
            user_id: User ID

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found
        """
        return await self.unsuspend_user(user_id)

    async def unsuspend_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Unsuspend a user's account.

        Args:
            user_id: User ID

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(str(user_id), "User")

        user.is_suspended = False
        user.suspension_reason = None
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("unsuspend_user", user_id, "User unsuspended")

        return {"message": "User unsuspended successfully"}

    async def _log_admin_action(
        self, action: str, target_id: UUID, notes: Optional[str] = None
    ) -> None:
        """
        Log admin action for audit trail.

        Args:
            action: Action performed
            target_id: ID of target entity
            notes: Optional notes
        """
        # In production, you would save this to an AuditLog model
        # For now, we'll just log it
        logger = __import__("logging").getLogger(__name__)
        logger.info(f"Admin action: {action} on {target_id} - Notes: {notes}")
