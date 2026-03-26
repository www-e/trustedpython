"""Listing status management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.enums import ListingStatus
from app.repositories.listing import ListingRepository
from app.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.services.listing_auth import ListingAuthService


class ListingStatusService:
    """Service for listing status transitions."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing status service.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)
        self.auth_service = ListingAuthService(db)

    async def publish_listing(
        self,
        listing_id: int,
        seller_id: int
    ) -> Listing:
        """
        Publish a listing (change status from DRAFT to ACTIVE).

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
            ValidationError: If listing is not in draft status
        """
        # Verify ownership
        listing = await self.auth_service.verify_ownership(listing_id, seller_id)

        # Check status
        if listing.status != ListingStatus.DRAFT:
            raise ValidationError("Only draft listings can be published")

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.ACTIVE)
        return await self.listing_repo.get_with_images(updated.id)

    async def pause_listing(
        self,
        listing_id: int,
        seller_id: int
    ) -> Listing:
        """
        Pause a listing (change status from ACTIVE to PAUSED).

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
            ValidationError: If listing is not active
        """
        # Verify ownership
        listing = await self.auth_service.verify_ownership(listing_id, seller_id)

        # Check status
        if listing.status != ListingStatus.ACTIVE:
            raise ValidationError("Only active listings can be paused")

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.PAUSED)
        return await self.listing_repo.get_with_images(updated.id)

    async def activate_listing(
        self,
        listing_id: int,
        seller_id: int
    ) -> Listing:
        """
        Activate a paused listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
            ValidationError: If listing is not paused
        """
        # Verify ownership
        listing = await self.auth_service.verify_ownership(listing_id, seller_id)

        # Check status
        if listing.status != ListingStatus.PAUSED:
            raise ValidationError("Only paused listings can be activated")

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.ACTIVE)
        return await self.listing_repo.get_with_images(updated.id)

    async def archive_listing(
        self,
        listing_id: int,
        seller_id: int
    ) -> Listing:
        """
        Archive a listing (change status to ARCHIVED).

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID

        Returns:
            Updated listing with images

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Verify ownership
        await self.auth_service.verify_ownership(listing_id, seller_id)

        # Update status
        updated = await self.listing_repo.update(listing_id, status=ListingStatus.ARCHIVED)
        return await self.listing_repo.get_with_images(updated.id)
