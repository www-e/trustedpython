"""
User Management Service for admin operations.

Handles all user-related admin operations including listing, verification,
suspension, banning, and searching users.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Integer, and_, case, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.account import Account
from app.models.content import Category, FAQItem, Game, PromoBanner
from app.models.deal import Deal, Payment
from app.models.listing import Listing
from app.models.mediator import Mediator, MediatorApplication
from app.models.review import Review
from app.models.user import User, UserProfile
from app.schemas.admin import (
    AnalyticsResponse,
    BlockedUsersResponse,
    CategoriesResponse,
    DashboardStatsResponse,
    DealListResponse,
    FAQResponse,
    GamesResponse,
    ListingModerationResponse,
    LoginHistoryItem,
    MediatorApplicationsResponse,
    MediatorListResponse,
    PromoBannersResponse,
    ReportsResponse,
    UserDetailResponse,
    UserListItem,
    UserListResponse,
    UserProfileInDetail,
    UserStatsInList,
)


class UserManagementService:
    """
    User management service for admin operations.

    Provides comprehensive user management functionality including listing,
    verification, suspension, banning, and searching users.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize UserManagementService.

        Args:
            db: Async database session
        """
        self.db = db

    async def list_all_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> UserListResponse:
        """
        List all users with filtering and pagination.

        Args:
            status: Filter by status (active, suspended, banned)
            role: Filter by role (user, mediator, admin)
            search: Search username/email
            page: Page number
            limit: Items per page

        Returns:
            UserListResponse: List of users with pagination
        """
        query = select(User).join(UserProfile).options(selectinload(User.profile))

        # Apply filters
        if status == "suspended":
            query = query.where(User.is_suspended == True)
        elif status == "banned":
            query = query.where(
                User.is_suspended == True
            )  # Banned users are also marked as suspended

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(User.username.ilike(search_term), User.email.ilike(search_term))
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query.order_by(desc(User.created_at)))
        users = result.scalars().all()

        # Transform to response format
        user_items = []
        for user in users:
            # Calculate user stats
            total_deals = (
                await self.db.scalar(
                    select(func.count(Deal.id)).where(
                        or_(Deal.buyer_id == user.id, Deal.seller_id == user.id)
                    )
                )
                or 0
            )
            listings_count = (
                await self.db.scalar(
                    select(func.count(Listing.id)).where(Listing.seller_id == user.id)
                )
                or 0
            )
            rating = float(user.profile.rating) if user.profile else 0.0

            user_items.append(
                UserListItem(
                    id=str(user.id),
                    username=user.username,
                    email=user.email,
                    phone=user.phone,
                    display_name=user.profile.display_name if user.profile else None,
                    avatar_url=user.profile.avatar_url if user.profile else None,
                    is_verified=user.profile.is_verified if user.profile else False,
                    is_suspended=user.is_suspended,
                    is_banned=False,  # This would come from a separate ban table
                    role="user",  # This would come from user role field
                    stats=UserStatsInList(
                        total_deals=total_deals,
                        rating=rating,
                        listings_count=listings_count,
                    ),
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                )
            )

        return UserListResponse(
            users=user_items, pagination={"page": page, "limit": limit, "total": total or 0}
        )

    async def get_user_details(self, user_id: UUID) -> UserDetailResponse:
        """
        Get detailed user information.

        Args:
            user_id: User ID

        Returns:
            UserDetailResponse: Detailed user information

        Raises:
            NotFoundException: If user not found
        """
        # Get user with profile
        result = await self.db.execute(
            select(User)
            .join(UserProfile)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(str(user_id), "User")

        # Get user statistics
        listings_count = (
            await self.db.scalar(select(func.count(Listing.id)).where(Listing.seller_id == user_id))
            or 0
        )
        active_deals = (
            await self.db.scalar(
                select(func.count(Deal.id)).where(
                    and_(
                        or_(Deal.buyer_id == user_id, Deal.seller_id == user_id),
                        Deal.status.in_(
                            ["pending", "awaiting_payment", "payment_submitted", "verified"]
                        ),
                    )
                )
            )
            or 0
        )

        # Get reports against user (would need a Report model)
        reports_against = 0

        # Get login history (would need a LoginHistory model)
        login_history: list[LoginHistoryItem] = []

        return UserDetailResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            phone=user.phone,
            display_name=user.profile.display_name if user.profile else None,
            avatar_url=user.profile.avatar_url if user.profile else None,
            is_verified=user.profile.is_verified if user.profile else False,
            is_email_verified=user.is_email_verified,
            is_suspended=user.is_suspended,
            suspension_reason=user.suspension_reason,
            is_banned=False,  # This would come from a separate ban table
            ban_reason=None,
            profile=UserProfileInDetail(
                bio=user.profile.bio if user.profile else None,
                user_role=user.profile.user_role if user.profile else "Trader",
                member_since=user.profile.member_since if user.profile else None,
                completed_deals=user.profile.completed_deals if user.profile else 0,
                rating=float(user.profile.rating) if user.profile else 0.0,
                accounts_sold=user.profile.accounts_sold if user.profile else 0,
                bought_count=user.profile.bought_count if user.profile else 0,
            ),
            listings=listings_count,
            active_deals=active_deals,
            reports_against=reports_against,
            login_history=login_history,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def verify_user(self, user_id: UUID, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a user's account.

        Args:
            user_id: User ID
            notes: Optional admin notes

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise NotFoundException(str(user_id), "User")

        profile.is_verified = True
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("verify_user", user_id, notes)

        return {"message": "User verified successfully"}

    async def suspend_user(
        self, user_id: UUID, reason: str, duration_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Suspend a user's account.

        Args:
            user_id: User ID
            reason: Suspension reason
            duration_days: Duration in days (null = indefinite)

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(str(user_id), "User")

        user.is_suspended = True
        user.suspension_reason = reason
        await self.db.commit()

        # Log admin action
        await self._log_admin_action(
            "suspend_user", user_id, f"Reason: {reason}, Duration: {duration_days} days"
        )

        return {"message": "User suspended successfully"}

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

    async def ban_user(self, user_id: UUID, reason: str) -> Dict[str, Any]:
        """
        Permanently ban a user.

        Args:
            user_id: User ID
            reason: Ban reason

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(str(user_id), "User")

        user.is_suspended = True
        user.suspension_reason = f"BANNED: {reason}"
        user.is_active = False
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("ban_user", user_id, f"Reason: {reason}")

        return {"message": "User banned successfully"}

    async def search_users(self, query: str, page: int = 1, limit: int = 20) -> UserListResponse:
        """
        Search users by username or email.

        Args:
            query: Search query
            page: Page number
            limit: Items per page

        Returns:
            UserListResponse: Search results
        """
        return await self.list_all_users(search=query, page=page, limit=limit)

    # ========================================================================
    # Helper Methods
    # ========================================================================

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
        pass
