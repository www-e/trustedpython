"""
Sell business logic service.

Handles listing creation, preview, image upload, category/game management,
publishing, and analytics for sellers.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

import io
from PIL import Image
from fastapi import UploadFile
from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.models.content import Category, Game
from app.models.deal import Deal
from app.models.listing import Listing
from app.models.user import User, UserProfile
from app.schemas.listing import (
    CategoryResponse,
    CreateListingRequest,
    GameResponse,
    ImageResponse,
    ListingDetailResponse,
    ListingResponse,
    PreviewListingData,
    PreviewListingRequest,
    PreviewListingResponse,
    PublishResponse,
    RecentActivity,
    SellAnalyticsData,
    SellAnalyticsResponse,
    TopPerformingListing,
    UpdateListingRequest,
)
from app.utils.storage import upload_file_to_storage


class SellService:
    """
    Sell service for seller operations.

    Provides methods for creating and managing listings, uploading images,
    handling categories/games, and providing seller analytics.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize sell service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_listing(self, user_id: UUID, data: CreateListingRequest) -> ListingResponse:
        """
        Create a new listing.

        Args:
            user_id: Seller UUID
            data: Listing creation data

        Returns:
            ListingResponse: Created listing

        Raises:
            ValidationException: If validation fails
            ForbiddenException: If account not verified
            RateLimitException: If rate limit exceeded
        """
        # Verify user is verified
        user = await self._get_user_by_id(user_id)
        if not user or not user.profile.is_verified:
            raise ForbiddenException("create listings (account not verified)")

        # Check rate limit (max 10 listings per day)
        await self._check_rate_limit(user_id)

        # Validate category exists
        category = await self._get_category_by_id(data.category_id)
        if not category:
            raise NotFoundException(str(data.category_id), "Category")

        # Validate premium tier permissions
        if data.is_premium and data.tier:
            await self._validate_premium_tier(user_id, data.tier)

        # Create listing
        listing = Listing(
            seller_id=user_id,
            title=data.title,
            price=float(data.price),
            game=data.game,
            category_id=data.category_id,
            description=data.description,
            status="draft",
            is_premium=data.is_premium,
            tier=data.tier or "Regular",
            views_count=0,
        )

        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)

        return self._listing_to_response(listing)

    async def preview_listing(self, data: PreviewListingRequest) -> PreviewListingResponse:
        """
        Preview how a listing will appear.

        Args:
            data: Preview data

        Returns:
            PreviewListingResponse: Preview data
        """
        # Format price
        formatted_price = f"${data.price:.2f}"

        # Get thumbnail (first image)
        thumbnail_url = None
        if data.image_urls:
            thumbnail_url = data.image_urls[0]

        # Estimate views based on premium tier
        estimated_views = None
        if data.is_premium:
            if data.tier == "Gold":
                estimated_views = 150
            elif data.tier == "Elite":
                estimated_views = 300
            else:
                estimated_views = 50
        else:
            estimated_views = 20

        preview_data = PreviewListingData(
            title=data.title,
            price=data.price,
            formatted_price=formatted_price,
            game=data.game,
            thumbnail_url=thumbnail_url,
            is_premium=data.is_premium,
            tier=data.tier,
            estimated_views=estimated_views,
        )

        return PreviewListingResponse(preview=preview_data)

    async def get_categories(self) -> List[CategoryResponse]:
        """
        Get all available categories.

        Returns:
            List[CategoryResponse]: Categories list
        """
        result = await self.db.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name)
        )
        categories = result.scalars().all()

        return [
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                icon=cat.icon,
                game=cat.game.name if cat.game else None,
                description=cat.description,
                listing_count=cat.listing_count,
            )
            for cat in categories
        ]

    async def get_games(self) -> List[GameResponse]:
        """
        Get all supported games.

        Returns:
            List[GameResponse]: Games list
        """
        result = await self.db.execute(
            select(Game).where(Game.is_active == True).order_by(Game.name)
        )
        games = result.scalars().all()

        return [
            GameResponse(
                id=game.id,
                name=game.name,
                slug=game.slug,
                icon_url=game.icon_url,
                banner_url=game.banner_url,
                active_listings=game.active_listings,
                avg_price=float(game.avg_price) if game.avg_price else None,
                popular=game.is_popular,
            )
            for game in games
        ]

    async def upload_images(
        self, user_id: UUID, files: List[tuple], filenames: List[str]
    ) -> List[ImageResponse]:
        """
        Upload listing images.

        Args:
            user_id: User UUID
            files: List of (filename, content, content_type) tuples
            filenames: List of original filenames

        Returns:
            List[ImageResponse]: Uploaded image data

        Raises:
            ValidationException: If validation fails
        """
        if len(files) > 10:
            raise ValidationException("Maximum 10 images allowed")

        images = []
        for i, (file_data, filename) in enumerate(zip(files, filenames)):
            # Get image dimensions using PIL
            img = Image.open(io.BytesIO(file_data))
            width, height = img.size

            # Create UploadFile object for storage upload
            file_obj = UploadFile(
                filename=filename,
                file=io.BytesIO(file_data),
            )

            # Upload to storage
            url = await upload_file_to_storage(file_obj, folder="listings")

            # Generate thumbnail URL (same path with _thumb suffix)
            thumbnail_url = url.rsplit(".", 1)[0] + "_thumb." + url.rsplit(".", 1)[1]

            images.append(
                ImageResponse(
                    id=uuid4(),
                    url=url,
                    thumbnail_url=thumbnail_url,
                    filename=filename,
                    size=len(file_data),
                    width=width,
                    height=height,
                )
            )

        return images

    async def update_listing(
        self, listing_id: UUID, user_id: UUID, data: UpdateListingRequest
    ) -> ListingResponse:
        """
        Update an existing listing.

        Args:
            listing_id: Listing UUID
            user_id: User UUID
            data: Update data

        Returns:
            ListingResponse: Updated listing

        Raises:
            NotFoundException: If listing not found
            ForbiddenException: If not listing owner
        """
        listing = await self._get_listing_by_id(listing_id)

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        if listing.seller_id != user_id:
            raise ForbiddenException("edit this listing")

        # Update fields
        if data.title is not None:
            listing.title = data.title
        if data.price is not None:
            listing.price = float(data.price)
        if data.game is not None:
            listing.game = data.game
        if data.category_id is not None:
            listing.category_id = data.category_id
        if data.description is not None:
            listing.description = data.description
        if data.is_premium is not None:
            listing.is_premium = data.is_premium
        if data.tier is not None:
            listing.tier = data.tier

        listing.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(listing)

        return self._listing_to_response(listing)

    async def publish_listing(self, listing_id: UUID, user_id: UUID) -> PublishResponse:
        """
        Publish a draft listing.

        Args:
            listing_id: Listing UUID
            user_id: User UUID

        Returns:
            PublishResponse: Published listing data

        Raises:
            NotFoundException: If listing not found
            ForbiddenException: If not listing owner
        """
        listing = await self._get_listing_by_id(listing_id)

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        if listing.seller_id != user_id:
            raise ForbiddenException("publish this listing")

        if listing.status not in ["draft", "expired"]:
            raise ValidationException(f"Cannot publish listing with status '{listing.status}'")

        listing.status = "active"
        listing.published_at = datetime.utcnow()
        listing.expired_at = datetime.utcnow() + timedelta(days=30)

        await self.db.commit()
        await self.db.refresh(listing)

        return PublishResponse(
            id=listing.id, status=listing.status, published_at=listing.published_at, unpublished_at=None
        )

    async def unpublish_listing(self, listing_id: UUID, user_id: UUID) -> PublishResponse:
        """
        Unpublish a listing (hide from marketplace).

        Args:
            listing_id: Listing UUID
            user_id: User UUID

        Returns:
            PublishResponse: Unpublished listing data

        Raises:
            NotFoundException: If listing not found
            ForbiddenException: If not listing owner
        """
        listing = await self._get_listing_by_id(listing_id)

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        if listing.seller_id != user_id:
            raise ForbiddenException("unpublish this listing")

        if listing.status != "active":
            raise ValidationException(f"Cannot unpublish listing with status '{listing.status}'")

        listing.status = "draft"
        listing.published_at = None

        await self.db.commit()
        await self.db.refresh(listing)

        return PublishResponse(
            id=listing.id, status=listing.status, unpublished_at=datetime.utcnow(), published_at=None
        )

    async def get_analytics(self, user_id: UUID) -> SellAnalyticsResponse:
        """
        Get sell analytics for user.

        Args:
            user_id: User UUID

        Returns:
            SellAnalyticsResponse: Analytics data
        """
        # Get listing stats
        total_listings = await self._count_user_listings(user_id)
        active_listings = await self._count_user_listings(user_id, status="active")
        sold_listings = await self._count_user_listings(user_id, status="sold")

        # Get views and revenue
        total_views = await self._get_total_views(user_id)
        total_revenue = await self._get_total_revenue(user_id)

        # Get avg time to sell
        avg_time_to_sell = await self._get_avg_time_to_sell(user_id)

        # Get top performing listing
        top_listing = await self._get_top_performing_listing(user_id)

        # Get recent activity
        recent_activity = await self._get_recent_activity(user_id)

        analytics_data = SellAnalyticsData(
            total_listings=total_listings,
            active_listings=active_listings,
            sold_listings=sold_listings,
            total_views=total_views,
            total_revenue=total_revenue,
            avg_time_to_sell=avg_time_to_sell,
            top_performing_listing=top_listing,
            recent_activity=recent_activity,
        )

        return SellAnalyticsResponse(analytics=analytics_data)

    # Helper Methods

    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by UUID with profile."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_listing_by_id(self, listing_id: UUID) -> Optional[Listing]:
        """Get listing by UUID."""
        result = await self.db.execute(select(Listing).where(Listing.id == listing_id))
        return result.scalar_one_or_none()

    async def _get_category_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get category by UUID."""
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def _check_rate_limit(self, user_id: UUID) -> None:
        """
        Check if user has exceeded rate limit for listing creation.

        Args:
            user_id: User UUID

        Raises:
            RateLimitException: If rate limit exceeded
        """
        # Count listings created in last 24 hours
        since = datetime.utcnow() - timedelta(days=1)

        result = await self.db.execute(
            select(func.count(Listing.id)).where(
                and_(Listing.seller_id == user_id, Listing.created_at >= since)
            )
        )
        count = result.scalar() or 0

        if count >= 10:
            raise RateLimitException(retry_after=86400)  # 24 hours

    async def _validate_premium_tier(self, user_id: UUID, tier: str) -> None:
        """
        Validate if user has permission for premium tier.

        Args:
            user_id: User UUID
            tier: Premium tier

        Raises:
            ForbiddenException: If not authorized for tier
        """
        pass

    async def _count_user_listings(self, user_id: UUID, status: Optional[str] = None) -> int:
        """Count user's listings by status."""
        query = select(func.count(Listing.id)).where(Listing.seller_id == user_id)

        if status:
            query = query.where(Listing.status == status)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_total_views(self, user_id: UUID) -> int:
        """Get total views for user's listings."""
        result = await self.db.execute(
            select(func.sum(Listing.views_count)).where(Listing.seller_id == user_id)
        )
        return result.scalar() or 0

    async def _get_total_revenue(self, user_id: UUID) -> float:
        """Get total revenue from user's sales."""
        result = await self.db.execute(
            select(func.sum(Deal.total_amount)).where(
                and_(Deal.seller_id == user_id, Deal.status == "completed")
            )
        )
        return float(result.scalar() or 0.0)

    async def _get_avg_time_to_sell(self, user_id: UUID) -> Optional[float]:
        """Get average days to sell for user's listings."""
        result = await self.db.execute(
            select(Deal, Listing).join(Listing, Deal.listing_id == Listing.id).where(
                and_(
                    Listing.seller_id == user_id,
                    Deal.status == "completed",
                    Deal.completed_at.isnot(None),
                    Listing.created_at.isnot(None),
                )
            )
        )
        deals_with_listings = result.all()

        if not deals_with_listings:
            return None

        total_days = 0.0
        count = 0
        for deal, listing in deals_with_listings:
            if deal.completed_at and listing.created_at:
                delta = deal.completed_at - listing.created_at
                total_days += delta.total_seconds() / 86400
                count += 1

        if count == 0:
            return None

        return round(total_days / count, 1)

    async def _get_top_performing_listing(self, user_id: UUID) -> Optional[TopPerformingListing]:
        """Get user's top performing listing."""
        result = await self.db.execute(
            select(Listing)
            .where(Listing.seller_id == user_id)
            .order_by(desc(Listing.views_count))
            .limit(1)
        )
        listing = result.scalar_one_or_none()

        if not listing:
            return None

        # Calculate sold_in_days from deal data
        sold_in_days = None
        if listing.id:
            deal_result = await self.db.execute(
                select(Deal).where(
                    and_(
                        Deal.listing_id == listing.id,
                        Deal.status == "completed",
                        Deal.completed_at.isnot(None),
                    )
                ).limit(1)
            )
            deal = deal_result.scalar_one_or_none()
            if deal and deal.completed_at:
                delta = deal.completed_at - listing.created_at
                sold_in_days = round(delta.total_seconds() / 86400, 1)

        return TopPerformingListing(
            id=listing.id, title=listing.title, views=listing.views_count, sold_in_days=sold_in_days
        )

    async def _get_recent_activity(self, user_id: UUID) -> List[RecentActivity]:
        """Get recent activity for user's listings."""
        activity_time = case(
            (Deal.completed_at.isnot(None), Deal.completed_at),
            else_=Deal.cancelled_at,
        )

        result = await self.db.execute(
            select(Deal, Listing).join(Listing, Deal.listing_id == Listing.id).where(
                and_(
                    Listing.seller_id == user_id,
                    Deal.status.in_(["completed", "cancelled"]),
                )
            ).order_by(desc(activity_time)).limit(5)
        )
        deals_with_listings = result.all()

        activities = []
        for deal, listing in deals_with_listings:
            ts = deal.completed_at or deal.cancelled_at
            if ts:
                activities.append(
                    RecentActivity(
                        action=f"listing_{deal.status}",
                        listing_title=listing.title,
                        timestamp=ts,
                    )
                )

        return activities

    def _listing_to_response(self, listing: Listing) -> ListingResponse:
        """Convert Listing model to response dict."""
        # Extract image URLs from listing's images relationship if it exists
        # Note: Requires images table and relationship on Listing model
        image_urls = (
            [img.url for img in listing.images]
            if hasattr(listing, "images") and listing.images
            else []
        )

        return ListingResponse(
            id=listing.id,
            title=listing.title,
            price=float(listing.price),
            game=listing.game or "",
            category_id=listing.category_id,
            description=listing.description,
            thumbnail_url=listing.thumbnail_url,
            image_urls=image_urls,
            status=listing.status,
            is_premium=listing.is_premium,
            tier=listing.tier,
            created_at=listing.created_at,
            views_count=listing.views_count,
        )
