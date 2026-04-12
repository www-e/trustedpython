"""
Listing management service for user profiles.

Handles CRUD operations for user's own listings within the profile context.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.listing import Listing
from app.schemas.common import PaginationSchema
from app.schemas.listing import (
    ProfileCreateListingRequest,
    ProfileUpdateListingRequest,
    UploadImageResponse,
    UserListingDetailResponse,
    UserListingResponse,
    UserListingsListResponse,
)

from .base import check_listing_rate_limit, get_listing


class ListingManagementService:
    """
    Service for managing user listings within profile context.

    This service handles:
    - Listing retrieval (user's own listings)
    - Listing creation
    - Listing updates
    - Listing deletion
    - Listing status management
    - Image uploads for listings
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize listing management service.

        Args:
            db: Database session
        """
        self.db = db

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
        await check_listing_rate_limit(self.db, user_id)

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
        listing = await get_listing(self.db, listing_id)

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
        listing = await get_listing(self.db, listing_id)

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
        listing = await get_listing(self.db, listing_id)

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
        listing = await get_listing(self.db, listing_id)

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
        import os

        # Validate file size (max 5MB)
        if len(file_data) > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB limit")

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError("Invalid file type. Only JPG, JPEG, PNG allowed")

        # Upload to storage
        from app.utils.storage import upload_file_to_storage
        
        upload_file = UploadFile(
            file=io.BytesIO(file_data),
            size=len(file_data),
            filename=filename,
            headers={"content-type": f"image/{file_ext.lstrip('.')}"},
        )
        image_url = await upload_file_to_storage(upload_file, folder="listings")
        image_id = str(uuid4())

        # Note: Malware scanning should be implemented before production
        return UploadImageResponse(
            id=image_id, url=image_url, filename=filename, size=len(file_data)
        )
