"""Listing authorization and ownership verification service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.repositories.listing import ListingRepository
from app.exceptions import NotFoundError, ForbiddenError


class ListingAuthService:
    """Service for listing authorization and ownership checks."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing auth service.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)

    async def verify_ownership(
        self,
        listing_id: int,
        user_id: int
    ) -> Listing:
        """
        Verify user owns the listing.

        Args:
            listing_id: Listing ID
            user_id: User ID to check

        Returns:
            Listing if user owns it

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user doesn't own the listing
        """
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        if listing.seller_id != user_id:
            raise ForbiddenError("You don't own this listing")

        return listing

    async def verify_ownership_or_admin(
        self,
        listing_id: int,
        user_id: int,
        is_admin: bool = False
    ) -> Listing:
        """
        Verify user owns the listing or is admin.

        Args:
            listing_id: Listing ID
            user_id: User ID to check
            is_admin: Whether user is admin

        Returns:
            Listing if user owns it or is admin

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user doesn't own the listing and is not admin
        """
        listing = await self.listing_repo.get(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")

        if listing.seller_id != user_id and not is_admin:
            raise ForbiddenError("You don't own this listing")

        return listing
