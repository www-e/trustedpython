"""Listing admin operations service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.repositories.listing import ListingRepository
from app.exceptions import NotFoundError


class ListingAdminService:
    """Service for listing admin operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing admin service.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)

    async def toggle_featured(self, listing_id: int) -> Listing:
        """
        Toggle the featured status of a listing (Admin only).

        Args:
            listing_id: Listing ID

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
        """
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Toggle featured status
        updated = await self.listing_repo.update(
            listing_id,
            is_featured=not listing.is_featured
        )
        await self.db.commit()
        return await self.listing_repo.get_with_images(updated.id)

    async def set_featured(self, listing_id: int, featured: bool) -> Listing:
        """
        Set the featured status of a listing (Admin only).

        Args:
            listing_id: Listing ID
            featured: Featured status to set

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
        """
        # Get listing
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        # Set featured status
        updated = await self.listing_repo.update(listing_id, is_featured=featured)
        await self.db.commit()
        return await self.listing_repo.get_with_images(updated.id)

    async def get_all_listings_admin(
        self,
        status=None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Listing]:
        """
        Get all listings for admin view.

        Args:
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of listings
        """
        if status:
            return await self.listing_repo.get_by_status(status, skip, limit)
        return await self.listing_repo.get_all(skip, limit)
