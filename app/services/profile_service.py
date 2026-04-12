"""Profile business logic service."""

import os
from datetime import date, datetime, timedelta
from typing import List, Optional, Sequence
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.deal import Deal
from app.models.listing import Listing
from app.models.user import User, UserProfile
from app.schemas.common import PaginationSchema
from app.schemas.listing import (
    ProfileCreateListingRequest,
    ProfileUpdateListingRequest,
    UploadImageResponse,
    UserListingDetailResponse,
    UserListingResponse,
    UserListingsListResponse,
)
from app.schemas.profile import (
    ListingSummary,
    PublicProfileResponse,
    TradeHistoryCounterparty,
    TradeHistoryItem,
    TradeHistoryListResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UploadAvatarResponse,
    UserProfileResponse,
    UserProfileStats,
    UserStatsResponse,
)
from app.utils.storage import upload_file_to_storage
from fastapi import UploadFile


class ProfileService:
    """Service for profile-related business logic."""

    def __init__(self, db: AsyncSession):
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
        result = await self.db.execute(
            select(User, UserProfile)
            .join(UserProfile, User.id == UserProfile.user_id)
            .where(User.id == user_id)
        )
        user_profile = result.first()

        if not user_profile:
            raise NotFoundError("User profile not found")

        user, profile = user_profile

        # Get stats
        stats = await self._calculate_user_stats(user_id)

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
            .where(or_(Deal.buyer_id == user_id, Deal.seller_id == user_id))
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
            recent_trades=await self._build_trade_history_items(recent_deals, user_id),
        )

    async def get_user_stats(self, user_id: UUID) -> UserStatsResponse:
        """
        Get detailed user statistics.

        Args:
            user_id: User ID

        Returns:
            UserStatsResponse: Detailed user statistics
        """
        profile = await self._get_profile(user_id)
        stats = await self._calculate_detailed_stats(user_id)

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
            trades=await self._build_trade_history_items(deals, user_id),
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
        profile = await self._get_profile(user_id)

        # Update fields if provided
        if data.display_name is not None:
            profile.display_name = data.display_name

        if data.phone is not None:
            # Update user phone too
            user = await self._get_user(user_id)
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
        # Validate file size (max 2MB)
        if len(file_data) > 2 * 1024 * 1024:
            raise ValidationError("File size exceeds 2MB limit")

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError("Invalid file type. Only JPG, JPEG, PNG allowed")

        # Upload to storage
        upload_file = UploadFile(
            file=io.BytesIO(file_data),
            size=len(file_data),
            filename=filename,
            headers={"content-type": f"image/{file_ext.lstrip('.')}"},
        )
        avatar_url = await upload_file_to_storage(upload_file, folder="avatars")

        # Update profile
        profile = await self._get_profile(user_id)
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
        user, profile = await self._get_user_and_profile(target_user_id)

        # Get public stats
        stats = await self._calculate_user_stats(target_user_id)

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

    async def get_user_listings(
        self, user_id: UUID, status: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> UserListingsListResponse:
        """
        Get user's listings with pagination.

        Args:
            user_id: User ID
            status: Filter by status (active, sold, expired)
            page: Page number
            limit: Items per page

        Returns:
            UserListingsListResponse: Paginated listings
        """
        # Build query
        query = select(Listing).where(Listing.seller_id == user_id)

        if status:
            query = query.where(Listing.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(Listing.created_at))
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        listings = result.scalars().all()

        # Build pagination
        pagination = PaginationSchema.create(page, limit, total)

        return UserListingsListResponse(
            listings=[
                UserListingResponse(
                    id=listing.id,
                    title=listing.title,
                    price=float(listing.price),
                    thumbnail_url=listing.thumbnail_url,
                    game=listing.game,
                    status=listing.status,
                    views_count=listing.views_count,
                    created_at=listing.created_at,
                    updated_at=listing.updated_at,
                )
                for listing in listings
            ],
            pagination={
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
            },
        )

    async def create_listing(
        self, user_id: UUID, data: ProfileCreateListingRequest
    ) -> UserListingResponse:
        """
        Create a new listing.

        Args:
            user_id: User ID
            data: Listing data

        Returns:
            UserListingResponse: Created listing
        """
        # Check rate limiting (max 10 listings per day)
        await self._check_listing_rate_limit(user_id)

        # Create listing
        listing = Listing(
            seller_id=user_id,
            title=data.title,
            price=data.price,
            game=data.game,
            description=data.description,
            thumbnail_url=data.thumbnail_url,
            status="active",
            is_premium=data.is_premium,
            tier=data.tier or "Regular",
        )

        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)

        return UserListingResponse(
            id=listing.id,
            title=listing.title,
            price=float(listing.price),
            thumbnail_url=listing.thumbnail_url,
            game=listing.game,
            status=listing.status,
            views_count=listing.views_count,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

    async def get_listing_details(self, listing_id: UUID) -> UserListingDetailResponse:
        """
        Get listing details.

        Args:
            listing_id: Listing ID

        Returns:
            UserListingDetailResponse: Listing details
        """
        listing = await self._get_listing(listing_id)

        return UserListingDetailResponse(
            id=listing.id,
            title=listing.title,
            price=float(listing.price),
            game=listing.game,
            description=listing.description,
            thumbnail_url=listing.thumbnail_url,
            image_urls=[img.url for img in getattr(listing, "images", [])] if hasattr(listing, "images") else [],
            status=listing.status,
            is_premium=listing.is_premium,
            tier=listing.tier,
            views_count=listing.views_count,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

    async def update_listing(
        self, listing_id: UUID, user_id: UUID, data: ProfileUpdateListingRequest
    ) -> UserListingResponse:
        """
        Update a listing.

        Args:
            listing_id: Listing ID
            user_id: User ID (for ownership check)
            data: Update data

        Returns:
            UserListingResponse: Updated listing
        """
        listing = await self._get_listing(listing_id)

        # Verify ownership
        if listing.seller_id != user_id:
            raise ForbiddenError("You can only edit your own listings")

        # Update fields
        if data.title is not None:
            listing.title = data.title
        if data.price is not None:
            listing.price = data.price
        if data.game is not None:
            listing.game = data.game
        if data.description is not None:
            listing.description = data.description
        if data.thumbnail_url is not None:
            listing.thumbnail_url = data.thumbnail_url
        if data.is_premium is not None:
            listing.is_premium = data.is_premium
        if data.tier is not None:
            listing.tier = data.tier

        listing.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(listing)

        return UserListingResponse(
            id=listing.id,
            title=listing.title,
            price=float(listing.price),
            thumbnail_url=listing.thumbnail_url,
            game=listing.game,
            status=listing.status,
            views_count=listing.views_count,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

    async def delete_listing(self, listing_id: UUID, user_id: UUID) -> dict:
        """
        Delete a listing.

        Args:
            listing_id: Listing ID
            user_id: User ID (for ownership check)

        Returns:
            dict: Success response
        """
        listing = await self._get_listing(listing_id)

        # Verify ownership
        if listing.seller_id != user_id:
            raise ForbiddenError("You can only delete your own listings")

        await self.db.delete(listing)
        await self.db.commit()

        return {"success": True, "message": "Listing deleted successfully"}

    async def update_listing_status(
        self, listing_id: UUID, user_id: UUID, status: str
    ) -> UserListingResponse:
        """
        Update listing status.

        Args:
            listing_id: Listing ID
            user_id: User ID (for ownership check)
            status: New status

        Returns:
            UserListingResponse: Updated listing
        """
        listing = await self._get_listing(listing_id)

        # Verify ownership
        if listing.seller_id != user_id:
            raise ForbiddenError("You can only update your own listings")

        # Validate status
        valid_statuses = {"active", "sold", "expired"}
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")

        listing.status = status
        listing.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(listing)

        return UserListingResponse(
            id=listing.id,
            title=listing.title,
            price=float(listing.price),
            thumbnail_url=listing.thumbnail_url,
            game=listing.game,
            status=listing.status,
            views_count=listing.views_count,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

    async def upload_listing_image(self, file_data: bytes, filename: str) -> UploadImageResponse:
        """
        Upload a listing image.

        Args:
            file_data: File data
            filename: Original filename

        Returns:
            UploadImageResponse: Uploaded image info
        """
        # Validate file size (max 5MB)
        if len(file_data) > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB limit")

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError("Invalid file type. Only JPG, JPEG, PNG allowed")

        # Upload to storage
        upload_file = UploadFile(
            file=io.BytesIO(file_data),
            size=len(file_data),
            filename=filename,
            headers={"content-type": f"image/{file_ext.lstrip('.')}"},
        )
        image_url = await upload_file_to_storage(upload_file, folder="listings")
        image_id = str(uuid4())

        return UploadImageResponse(
            id=image_id, url=image_url, filename=filename, size=len(file_data)
        )

    # Helper methods

    async def _get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user

    async def _get_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile by user ID."""
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundError("User profile not found")
        return profile

    async def _get_user_and_profile(self, user_id: UUID) -> tuple[User, UserProfile]:
        """Get user and profile together."""
        result = await self.db.execute(
            select(User, UserProfile)
            .join(UserProfile, User.id == UserProfile.user_id)
            .where(User.id == user_id)
        )
        user_profile = result.first()
        if not user_profile:
            raise NotFoundError("User not found")
        user, profile = user_profile
        return user, profile

    async def _get_listing(self, listing_id: UUID) -> Listing:
        """Get listing by ID."""
        result = await self.db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()
        if not listing:
            raise NotFoundError("Listing not found")
        return listing

    async def _calculate_user_stats(self, user_id: UUID) -> dict:
        """Calculate basic user stats."""
        # Count completed deals as buyer
        bought_result = await self.db.execute(
            select(func.count(Deal.id)).where(
                and_(Deal.buyer_id == user_id, Deal.status == "completed")
            )
        )
        bought_count = bought_result.scalar() or 0

        # Count completed deals as seller
        sold_result = await self.db.execute(
            select(func.count(Deal.id)).where(
                and_(Deal.seller_id == user_id, Deal.status == "completed")
            )
        )
        accounts_sold = sold_result.scalar() or 0

        # Total completed deals
        completed_deals = bought_count + accounts_sold

        return {
            "completed_deals": completed_deals,
            "accounts_sold": accounts_sold,
            "bought_count": bought_count,
        }

    async def _calculate_detailed_stats(self, user_id: UUID) -> dict:
        """Calculate detailed user stats."""
        basic_stats = await self._calculate_user_stats(user_id)

        # Calculate total revenue (as seller)
        revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Deal.total_amount), 0)).where(
                and_(Deal.seller_id == user_id, Deal.status == "completed")
            )
        )
        total_revenue = revenue_result.scalar() or 0

        # Calculate average deal value
        completed_deals = basic_stats["completed_deals"]
        avg_deal_value = float(total_revenue) / completed_deals if completed_deals > 0 else None

        # Calculate success rate (completed / total deals)
        total_deals_result = await self.db.execute(
            select(func.count(Deal.id)).where(
                or_(Deal.buyer_id == user_id, Deal.seller_id == user_id)
            )
        )
        total_deals = total_deals_result.scalar() or 0
        success_rate = (completed_deals / total_deals * 100) if total_deals > 0 else 100.0

        return {
            **basic_stats,
            "total_revenue": float(total_revenue) if total_revenue else None,
            "avg_deal_value": avg_deal_value,
            "success_rate": round(success_rate, 2),
            "response_time_avg": None,  # Requires chat analytics table - future enhancement
        }

    async def _build_trade_history_items(
        self, deals: Sequence[Deal], user_id: UUID
    ) -> List[TradeHistoryItem]:
        """Build trade history items from deals."""
        items = []

        for deal in deals:
            # Determine role and counterparty
            if deal.buyer_id == user_id:
                role = "buyer"
                counterparty_id = deal.seller_id
            else:
                role = "seller"
                counterparty_id = deal.buyer_id

            # Get counterparty info
            counterparty_result = await self.db.execute(
                select(User, UserProfile)
                .join(UserProfile, User.id == UserProfile.user_id)
                .where(User.id == counterparty_id)
            )
            counterparty_data = counterparty_result.first()

            if counterparty_data:
                counterparty_user, counterparty_profile = counterparty_data
                counterparty = TradeHistoryCounterparty(
                    username=counterparty_user.username, avatar_url=counterparty_profile.avatar_url
                )
            else:
                counterparty = TradeHistoryCounterparty(username="Unknown User", avatar_url=None)

            # Get title from listing or account
            title = (
                deal.listing.title
                if deal.listing
                else deal.account.title if deal.account else "Trade"
            )

            items.append(
                TradeHistoryItem(
                    id=deal.id,
                    title=title,
                    price=float(deal.total_amount),
                    status=deal.status,
                    timestamp=deal.created_at,
                    game=deal.listing.game if deal.listing else None,
                    counterparty=counterparty,
                    role=role,
                )
            )

        return items

    async def _check_listing_rate_limit(self, user_id: UUID) -> None:
        """Check if user has exceeded listing creation rate limit."""
        # Count listings created in last 24 hours
        since = datetime.utcnow() - timedelta(days=1)

        count_result = await self.db.execute(
            select(func.count(Listing.id)).where(
                and_(Listing.seller_id == user_id, Listing.created_at >= since)
            )
        )
        count = count_result.scalar() or 0

        if count >= 10:
            raise ValidationError("Rate limit exceeded: Maximum 10 listings per day")
