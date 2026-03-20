"""Listing service - business logic layer."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingImage
from app.models.enums import ListingStatus
from app.repositories.listing import ListingRepository, ListingImageRepository
from app.schemas.listing import ListingCreate, ListingUpdate, ListingImageCreate
from app.exceptions import (
    NotFoundError,
    ForbiddenError,
    ValidationError
)


class ListingService:
    """Service for listing-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing service.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)
        self.image_repo = ListingImageRepository(db)

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
            Created listing

        Raises:
            NotFoundError: If category not found
            ValidationError: If data is invalid
        """
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
            status=ListingStatus.DRAFT  # New listings start as draft
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
            await self.listing_repo.increment_views(listing_id)

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
            Updated listing

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Check ownership
        if listing.seller_id != seller_id:
            raise ForbiddenError("You don't own this listing")

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
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Check ownership
        if listing.seller_id != seller_id:
            raise ForbiddenError("You don't own this listing")

        # Delete listing (images will be cascade deleted)
        return await self.listing_repo.delete(listing_id)

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

    async def add_listing_image(
        self,
        listing_id: int,
        seller_id: int,
        image_data: ListingImageCreate
    ) -> ListingImage:
        """
        Add an image to a listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID (for ownership check)
            image_data: Image data

        Returns:
            Created image

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Get listing to verify ownership
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        if listing.seller_id != seller_id:
            raise ForbiddenError("You don't own this listing")

        # Create image
        image = await self.image_repo.create(
            listing_id=listing_id,
            image_url=image_data.image_url,
            caption=image_data.caption,
            sort_order=image_data.sort_order,
            is_primary=image_data.is_primary
        )

        return image

    async def publish_listing(self, listing_id: int, seller_id: int) -> Listing:
        """
        Publish a listing (change status from DRAFT to ACTIVE).

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
            ValidationError: If listing is not in draft status
        """
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Check ownership
        if listing.seller_id != seller_id:
            raise ForbiddenError("You don't own this listing")

        # Check status
        if listing.status != ListingStatus.DRAFT:
            raise ValidationError("Only draft listings can be published")

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.ACTIVE)
        return await self.listing_repo.get_with_images(updated.id)

    async def pause_listing(self, listing_id: int, seller_id: int) -> Listing:
        """
        Pause a listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Check ownership
        if listing.seller_id != seller_id:
            raise ForbiddenError("You don't own this listing")

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.PAUSED)
        return await self.listing_repo.get_with_images(updated.id)
