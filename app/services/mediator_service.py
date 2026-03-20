"""Mediator service."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.repositories.listing_mediator import ListingMediatorRepository
from app.core.exceptions import ValidationError


class MediatorService:
    """Service for mediator-related business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize mediator service."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.listing_mediator_repo = ListingMediatorRepository(db)

    async def get_available_mediators(
        self,
        min_rating: float = 0.0,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get list of available mediators.

        Args:
            min_rating: Minimum rating (default 0.0)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of mediator users
        """
        if not 0.0 <= min_rating <= 5.0:
            raise ValidationError("Rating must be between 0.0 and 5.0")

        mediators = await self.user_repo.get_mediators(
            min_rating=min_rating,
            skip=offset,
            limit=limit
        )

        return mediators

    async def can_mediator_meditate_listing(
        self,
        listing_id: int,
        mediator_id: int
    ) -> bool:
        """
        Check if a mediator can mediate a listing.

        Args:
            listing_id: Listing ID
            mediator_id: Mediator user ID

        Returns:
            True if mediator can mediate, False otherwise
        """
        # Check if mediator is actually a mediator
        mediator = await self.user_repo.get(mediator_id)
        if not mediator or mediator.role != UserRole.MEDIATOR:
            return False

        # Check if mediator is in listing's allowed mediators
        return await self.listing_mediator_repo.mediator_can_meditate(
            listing_id,
            mediator_id
        )

    async def get_mediator_stats(self, mediator_id: int) -> dict:
        """
        Get mediator statistics.

        Args:
            mediator_id: Mediator user ID

        Returns:
            Mediator stats dict
        """
        mediator = await self.user_repo.get(mediator_id)
        if not mediator or mediator.role != UserRole.MEDIATOR:
            return None

        return {
            "id": mediator.id,
            "username": mediator.username,
            "rating": float(mediator.rating),
            "completed_deals": mediator.completed_deals,
            "total_deals": mediator.total_deals_as_seller + mediator.total_deals_as_buyer,
        }
