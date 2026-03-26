"""Listing service - core business logic layer."""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingImage
from app.repositories.listing import ListingRepository, ListingImageRepository
from app.schemas.listing import ListingCreate, ListingUpdate
from app.exceptions import NotFoundError
from app.services.listing_auth import ListingAuthService
from app.services.listing_status import ListingStatusService
from app.services.listing_image import ListingImageService
from app.services.listing_admin import ListingAdminService


class ListingService:
    """Service for listing-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing service with focused sub-services.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)
        self.image_repo = ListingImageRepository(db)

        # Sub-services for specific concerns
        self.auth = ListingAuthService(db)
        self.status = ListingStatusService(db)
        self.images = ListingImageService(db)
        self.admin = ListingAdminService(db)

    # Core CRUD Operations

    async def create_listing(
        self,
        seller_id: int,
        listing_data: ListingCreate
    ) -> Listing:
        """
        Create a new listing.

        Args:
            seller_id: Seller user ID
            listing_data: Listing creation data

        Returns:
            Created listing with images

        Raises:
            NotFoundError: If category not found
        """
        from app.models.enums import ListingStatus

        # Create listing
        listing = await self.listing_repo.create(
            seller_id=seller_id,
            category_id=listing_data.category_id,
            title=listing_data.title,
            description=listing_data.description,
            game_type=listing_data.game_type,
            level=listing_data.level,
            rank=listing_data.rank,
            server=listing_data.server,
            skins_count=listing_data.skins_count,
            characters_count=listing_data.characters_count,
            price=listing_data.price,
            is_featured=listing_data.is_featured,
            status=ListingStatus.DRAFT
        )

        # Create images if provided
        if listing_data.images:
            for i, image_data in enumerate(listing_data.images):
                await self.image_repo.create(
                    listing_id=listing.id,
                    image_url=image_data.image_url,
                    caption=image_data.caption,
                    sort_order=image_data.sort_order or i,
                    is_primary=image_data.is_primary or (i == 0)
                )

        # Reload listing with images
        return await self.listing_repo.get_with_images(listing.id)

    async def get_listing(self, listing_id: int, increment_views: bool = True) -> Listing:
        """
        Get a listing by ID.

        Args:
            listing_id: Listing ID
            increment_views: Whether to increment view count

        Returns:
            Listing with images

        Raises:
            NotFoundError: If listing not found
        """
        listing = await self.listing_repo.get_with_images(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        if increment_views:
            listing.views_count += 1
            await self.db.flush()

        return listing

    async def get_all_listings(
        self,
        active_only: bool = True,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Get all listings with optional filters.

        Args:
            active_only: Only return active listings
            category_id: Filter by category
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of listings
        """
        if active_only:
            if category_id:
                return await self.listing_repo.get_by_category(category_id, skip, limit)
            return await self.listing_repo.get_active_listings(skip, limit)
        return await self.listing_repo.get_all(skip, limit)

    async def get_seller_listings(
        self,
        seller_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Get listings by seller.

        Args:
            seller_id: Seller user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of seller's listings
        """
        return await self.listing_repo.get_by_seller(seller_id, skip, limit)

    async def update_listing(
        self,
        listing_id: int,
        seller_id: int,
        listing_data: ListingUpdate
    ) -> Listing:
        """
        Update a listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID (for ownership check)
            listing_data: Update data

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Verify ownership
        await self.auth.verify_ownership(listing_id, seller_id)

        # Build update dict with non-None values
        update_data = {
            k: v for k, v in listing_data.model_dump().items()
            if v is not None
        }

        # Update listing
        updated_listing = await self.listing_repo.update(listing_id, **update_data)
        return await self.listing_repo.get_with_images(updated_listing.id)

    async def delete_listing(
        self,
        listing_id: int,
        seller_id: int
    ) -> bool:
        """
        Delete a listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID (for ownership check)

        Returns:
            True if deleted

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Verify ownership
        await self.auth.verify_ownership(listing_id, seller_id)

        # Delete listing (images will be cascade deleted)
        return await self.listing_repo.delete(listing_id)

    # Search Operations

    async def search_listings(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        game_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Search listings with filters.

        Args:
            query: Search query
            category_id: Filter by category
            game_type: Filter by game type
            min_price: Minimum price
            max_price: Maximum price
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching listings
        """
        return await self.listing_repo.search(
            query=query or "",
            category_id=category_id,
            game_type=game_type,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit
        )

    async def get_featured_listings(self, limit: int = 10) -> List[Listing]:
        """
        Get featured listings.

        Args:
            limit: Maximum number of listings to return

        Returns:
            List of featured listings
        """
        return await self.listing_repo.get_featured_listings(limit)

    # Delegate methods to sub-services

    async def add_listing_image(self, listing_id: int, seller_id: int, image_data) -> ListingImage:
        """Add image to listing - delegates to image service."""
        from app.models.listing import ListingImage
        return await self.images.add_image(listing_id, seller_id, image_data)

    async def publish_listing(self, listing_id: int, seller_id: int) -> Listing:
        """Publish listing - delegates to status service."""
        return await self.status.publish_listing(listing_id, seller_id)

    async def pause_listing(self, listing_id: int, seller_id: int) -> Listing:
        """Pause listing - delegates to status service."""
        return await self.status.pause_listing(listing_id, seller_id)

    async def toggle_featured(self, listing_id: int) -> Listing:
        """Toggle featured status - delegates to admin service."""
        return await self.admin.toggle_featured(listing_id)
