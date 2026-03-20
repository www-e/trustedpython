"""Deal service for business logic."""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal, DealStatus
from app.models.listing import Listing
from app.models.user import User
from app.models.enums import UserRole
from app.repositories.deal import DealRepository
from app.repositories.listing_mediator import ListingMediatorRepository
from app.repositories.listing import ListingRepository
from app.schemas.deal import DealCreate, DealUpdate
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError


class DealService:
    """Service for deal-related business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize deal service."""
        self.db = db
        self.deal_repo = DealRepository(Deal, db)
        self.listing_mediator_repo = ListingMediatorRepository(db)
        self.listing_repo = ListingRepository(Listing, db)

    async def create_deal(
        self,
        listing_id: int,
        buyer_id: int,
        data: DealCreate
    ) -> Deal:
        """
        Create a new deal (buyer initiates purchase).

        Args:
            listing_id: Listing ID
            buyer_id: Buyer user ID
            data: Deal creation data

        Returns:
            Created deal

        Raises:
            NotFoundError: If listing not found
            ValidationError: If listing is not available
            ForbiddenError: If buyer tries to buy their own listing
        """
        # Get listing
        listing = await self.listing_repo.get_with_images(listing_id)
        if not listing:
            raise NotFoundError("Listing not found")

        # Check if listing is active
        if listing.status != "active":
            raise ValidationError("Can only buy active listings")

        # Check buyer is not the seller
        if listing.seller_id == buyer_id:
            raise ForbiddenError("Cannot buy your own listing")

        # Create deal
        deal_data = data.model_dump()
        deal_data['listing_id'] = listing_id
        deal_data['buyer_id'] = buyer_id
        deal_data['seller_id'] = listing.seller_id
        deal_data['price'] = listing.price  # Use listing price

        deal = await self.deal_repo.create(**deal_data)

        return deal

    async def get_deal(self, deal_id: int) -> Deal:
        """Get deal by ID with relations."""
        deal = await self.deal_repo.get_with_relations(deal_id)
        if not deal:
            raise NotFoundError("Deal not found")
        return deal

    async def get_user_deals(
        self,
        user_id: int,
        as_buyer: bool = False,
        as_seller: bool = False,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Deal]:
        """Get deals for a user."""
        # If neither specified, get both
        if not as_buyer and not as_seller:
            return await self.deal_repo.get_by_user(
                user_id=user_id,
                status=status,
                limit=limit,
                offset=offset
            )

        return await self.deal_repo.get_by_user(
            user_id=user_id,
            as_buyer=as_buyer,
            as_seller=as_seller,
            status=status,
            limit=limit,
            offset=offset
        )

    async def update_deal_status(
        self,
        deal_id: int,
        status: DealStatus,
        mediator_id: Optional[int] = None
    ) -> Deal:
        """
        Update deal status (mediator or admin only).

        Args:
            deal_id: Deal ID
            status: New status
            mediator_id: Optional mediator ID

        Returns:
            Updated deal
        """
        deal = await self.get_deal(deal)
        deal.status = status

        if mediator_id is not None:
            deal.mediator_id = mediator_id

        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def assign_mediator(
        self,
        deal_id: int,
        mediator_id: int
    ) -> Deal:
        """
        Assign a mediator to a deal.

        Args:
            deal_id: Deal ID
            mediator_id: Mediator user ID

        Returns:
            Updated deal

        Raises:
            NotFoundError: If deal or mediator not found
            ValidationError: If mediator is not in listing's allowed mediators
        """
        deal = await self.get_deal(deal_id)

        # Check if mediator is allowed for this listing
        can_meditate = await self.listing_mediator_repo.mediator_can_meditate(
            deal.listing_id,
            mediator_id
        )

        if not can_meditate:
            raise ValidationError("This mediator is not allowed to mediate this listing")

        deal.mediator_id = mediator_id
        deal.status = DealStatus.IN_PROGRESS

        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def complete_deal(
        self,
        deal_id: int,
        buyer_rating: Optional[float] = None,
        seller_rating: Optional[float] = None
    ) -> Deal:
        """
        Complete a deal and update user stats.

        Args:
            deal_id: Deal ID
            buyer_rating: Optional rating for buyer
            seller_rating: Optional rating for seller

        Returns:
            Completed deal
        """
        deal = await self.get_deal(deal_id)
        deal.status = DealStatus.COMPLETED

        # Update user stats would happen here
        # For now, just mark as completed

        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def cancel_deal(self, deal_id: int, user_id: int) -> Deal:
        """
        Cancel a deal (buyer or seller only).

        Args:
            deal_id: Deal ID
            user_id: User ID requesting cancellation

        Returns:
            Cancelled deal

        Raises:
            ForbiddenError: If user is not buyer or seller
        """
        deal = await self.get_deal(deal_id)

        # Only buyer or seller can cancel
        if deal.buyer_id != user_id and deal.seller_id != user_id:
            raise ForbiddenError("Only buyer or seller can cancel the deal")

        deal.status = DealStatus.CANCELLED

        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def get_pending_deals(self, limit: int = 100) -> List[Deal]:
        """Get all pending deals awaiting mediator assignment."""
        return await self.deal_repo.get_pending_deals(limit=limit)

    async def count_user_deals(
        self,
        user_id: int,
        as_buyer: bool = False,
        as_seller: bool = False,
        status: Optional[str] = None
    ) -> int:
        """Count deals for a user."""
        return await self.deal_repo.count_by_user(
            user_id=user_id,
            as_buyer=as_buyer,
            as_seller=as_seller,
            status=status
        )
