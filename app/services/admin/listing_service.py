"""
Listing Moderation Service for admin operations on listings.

Handles listing approval, rejection, removal, and retrieval of pending listings.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.listing import Listing
from app.models.user import User, UserProfile
from app.schemas.admin import ListingInModeration, ListingModerationResponse, SellerInListing


class ListingModerationService:
    """
    Service for listing moderation operations.

    Provides functionality for managing listing lifecycle including
    approval, rejection, removal, and viewing pending listings.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the listing moderation service.

        Args:
            db: Database session for async operations
        """
        self.db = db

    async def get_pending_listings(
        self, page: int = 1, limit: int = 20
    ) -> ListingModerationResponse:
        """
        Get listings awaiting approval.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            ListingModerationResponse: Pending listings
        """
        # Get total count
        total = await self.db.scalar(
            select(func.count(Listing.id)).where(Listing.status == "pending")
        )

        # Get pending listings
        result = await self.db.execute(
            select(Listing)
            .join(User, Listing.seller_id == User.id)
            .join(UserProfile, User.id == UserProfile.user_id)
            .where(Listing.status == "pending")
            .order_by(Listing.created_at)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        listings = result.scalars().all()

        # Transform to response format
        listing_items = []
        for listing in listings:
            waiting_hours = (datetime.now(timezone.utc) - listing.created_at).total_seconds() / 3600

            listing_items.append(
                ListingInModeration(
                    id=str(listing.id),
                    title=listing.title,
                    price=float(listing.price),
                    game=listing.game,
                    seller=SellerInListing(
                        id=str(listing.seller_id),
                        username=listing.seller.username,
                        is_verified=(
                            listing.seller.profile.is_verified if listing.seller.profile else False
                        ),
                    ),
                    status=listing.status,
                    image_urls=[listing.thumbnail_url] if listing.thumbnail_url else [],
                    created_at=listing.created_at,
                    waiting_hours=round(waiting_hours, 1),
                )
            )

        return ListingModerationResponse(
            listings=listing_items, pagination={"page": page, "limit": limit, "total": total or 0}
        )

    async def approve_listing(
        self, listing_id: UUID, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a pending listing.

        Args:
            listing_id: Listing ID
            notes: Optional admin notes

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If listing not found
        """
        result = await self.db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        listing.status = "active"
        listing.published_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("approve_listing", listing_id, notes)

        return {"message": "Listing approved successfully"}

    async def reject_listing(self, listing_id: UUID, reason: str) -> Dict[str, Any]:
        """
        Reject a listing with reason.

        Args:
            listing_id: Listing ID
            reason: Rejection reason

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If listing not found
        """
        result = await self.db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        listing.status = "rejected"
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("reject_listing", listing_id, f"Reason: {reason}")

        return {"message": "Listing rejected successfully"}

    async def remove_listing(self, listing_id: UUID) -> Dict[str, Any]:
        """
        Remove a listing from platform.

        Args:
            listing_id: Listing ID

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If listing not found
        """
        result = await self.db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise NotFoundException(str(listing_id), "Listing")

        await self.db.delete(listing)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("remove_listing", listing_id, "Listing removed")

        return {"message": "Listing removed successfully"}

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
        logger = __import__("logging").getLogger(__name__)
        logger.info(f"Admin action: {action} on {target_id} - Notes: {notes}")
