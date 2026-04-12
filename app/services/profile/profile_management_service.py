"""
Profile management service.

Handles user profile CRUD operations, stats calculation, and trade history.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.deal import Deal
from app.models.listing import Listing
from app.models.user import User, UserProfile
from app.schemas.common import PaginationSchema
from app.schemas.profile import (
    ListingSummary,
    PublicProfileResponse,
    TradeHistoryListResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UploadAvatarResponse,
    UserProfileResponse,
    UserProfileStats,
    UserStatsResponse,
)

from .base import (
    build_trade_history_items,
    calculate_detailed_stats,
    calculate_user_stats,
    get_profile,
    get_user,
    get_user_and_profile,
)


class ProfileManagementService:
    """
    Service for user profile management operations.

    This service handles:
    - User profile retrieval (current and public)
    - Profile updates
    - Avatar uploads
    - User statistics
    - Trade history
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize profile management service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_current_profile(self, user_id: UUID) -> UserProfileResponse:
        """
        Get current user's full profile.

        Args:
            user_id: Current user ID

        Returns:
            UserProfileResponse: Full user profile with stats and recent activity
        """
        # Fetch user and profile
        user, profile = await get_user_and_profile(self.db, user_id)

        # Get stats
        stats = await calculate_user_stats(self.db, user_id)

        # Get recent listings (last 5)
        recent_listings_result = await self.db.execute(
            select(Listing)
            .where(Listing.seller_id == user_id)
            .order_by(desc(Listing.created_at))
            .limit(5)
        )
        recent_listings = recent_listings_result.scalars().all()

        # Get recent trades (last 5)
        recent_trades_result = await self.db.execute(
            select(Deal)
            .where(Deal.buyer_id == user_id, Deal.seller_id == user_id)
            .order_by(desc(Deal.created_at))
            .limit(5)
        )
        recent_deals = recent_trades_result.scalars().all()

        # Build response
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            user_role=profile.user_role,
            is_verified=profile.is_verified,
            member_since=profile.member_since or user.created_at.date(),
            stats=UserProfileStats(
                completed_deals=stats.get("completed_deals", 0),
                rating=float(profile.rating),
                accounts_sold=stats.get("accounts_sold", 0),
                bought_count=stats.get("bought_count", 0),
            ),
            recent_listings=[
                ListingSummary(
                    id=listing.id,
                    title=listing.title,
                    price=float(listing.price),
                    thumbnail_url=listing.thumbnail_url,
                    game=listing.game,
                    status=listing.status,
                )
                for listing in recent_listings
            ],
            recent_trades=await build_trade_history_items(self.db, recent_deals, user_id),
        )

    async def get_user_stats(self, user_id: UUID) -> UserStatsResponse:
        """
        Get detailed user statistics.

        Args:
            user_id: User ID

        Returns:
            UserStatsResponse: Detailed user statistics
        """
        profile = await get_profile(self.db, user_id)
        stats = await calculate_detailed_stats(self.db, user_id)

        return UserStatsResponse(
            completed_deals=stats.get("completed_deals", 0),
            rating=float(profile.rating),
            accounts_sold=stats.get("accounts_sold", 0),
            bought_count=stats.get("bought_count", 0),
            total_revenue=stats.get("total_revenue"),
            avg_deal_value=stats.get("avg_deal_value"),
            success_rate=stats.get("success_rate", 100.0),
            response_time_avg=stats.get("response_time_avg"),
            member_since=profile.member_since or profile.user.created_at.date(),
        )

    async def get_trade_history(
        self, user_id: UUID, status: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> TradeHistoryListResponse:
        """
        Get user's trade history with pagination.

        Args:
            user_id: User ID
            status: Filter by status (completed, pending, cancelled)
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            TradeHistoryListResponse: Paginated trade history
        """
        from sqlalchemy import func, or_

        # Build query
        query = select(Deal).where(or_(Deal.buyer_id == user_id, Deal.seller_id == user_id))

        if status:
            query = query.where(Deal.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(Deal.created_at))
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        deals = result.scalars().all()

        # Build pagination info
        pagination = PaginationSchema.create(page, limit, total)

        return TradeHistoryListResponse(
            trades=await build_trade_history_items(self.db, deals, user_id),
            pagination={
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
            },
        )

    async def update_profile(
        self, user_id: UUID, data: UpdateProfileRequest
    ) -> UpdateProfileResponse:
        """
        Update user profile.

        Args:
            user_id: User ID
            data: Update data

        Returns:
            UpdateProfileResponse: Updated profile data
        """
        profile = await get_profile(self.db, user_id)

        # Update fields if provided
        if data.display_name is not None:
            profile.display_name = data.display_name

        if data.phone is not None:
            # Update user phone too
            user = await get_user(self.db, user_id)
            user.phone = data.phone

        if data.bio is not None:
            profile.bio = data.bio

        if data.user_role is not None:
            profile.user_role = data.user_role

        profile.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(profile)

        return UpdateProfileResponse(
            id=profile.user_id,
            display_name=profile.display_name,
            phone=profile.user.phone if profile.user else None,
            bio=profile.bio,
            updated_at=profile.updated_at,
        )

    async def upload_avatar(
        self, user_id: UUID, file_data: bytes, filename: str
    ) -> UploadAvatarResponse:
        """
        Upload user avatar.

        Args:
            user_id: User ID
            file_data: File data
            filename: Original filename

        Returns:
            UploadAvatarResponse: Avatar URL
        """
        import os

        # Validate file size (max 2MB)
        if len(file_data) > 2 * 1024 * 1024:
            raise ValidationError("File size exceeds 2MB limit")

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError("Invalid file type. Only JPG, JPEG, PNG allowed")

        # TODO: Implement actual upload to MinIO/S3
        # For now, generate a mock URL
        avatar_url = f"https://storage.example.com/avatars/{user_id}/{filename}"

        # Update profile
        profile = await get_profile(self.db, user_id)
        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()

        await self.db.commit()

        return UploadAvatarResponse(avatar_url=avatar_url)

    async def get_public_profile(self, target_user_id: UUID) -> PublicProfileResponse:
        """
        Get public profile of another user.

        Args:
            target_user_id: Target user ID

        Returns:
            PublicProfileResponse: Public profile (no sensitive data)
        """
        user, profile = await get_user_and_profile(self.db, target_user_id)

        # Get public stats
        stats = await calculate_user_stats(self.db, target_user_id)

        return PublicProfileResponse(
            id=user.id,
            username=user.username,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            user_role=profile.user_role,
            is_verified=profile.is_verified,
            member_since=profile.member_since or user.created_at.date(),
            stats=UserProfileStats(
                completed_deals=stats.get("completed_deals", 0),
                rating=float(profile.rating),
                accounts_sold=stats.get("accounts_sold", 0),
                bought_count=stats.get("bought_count", 0),
            ),
        )
