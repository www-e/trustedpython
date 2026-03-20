"""ListingMediator repository."""

from typing import List
from sqlalchemy import select, delete

from app.models.listing_mediator import ListingMediator
from app.repositories.base import BaseRepository


class ListingMediatorRepository(BaseRepository[ListingMediator]):
    """Repository for ListingMediator model."""

    async def get_by_listing(self, listing_id: int) -> List[ListingMediator]:
        """Get all mediator associations for a listing."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.listing_id == listing_id)
        )
        return list(result.scalars().all())

    async def get_by_mediator(self, mediator_id: int) -> List[ListingMediator]:
        """Get all listing associations for a mediator."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.mediator_id == mediator_id)
        )
        return list(result.scalars().all())

    async def create_associations(
        self,
        listing_id: int,
        mediator_ids: List[int]
    ) -> List[ListingMediator]:
        """
        Create mediator associations for a listing.

        Args:
            listing_id: Listing ID
            mediator_ids: List of mediator IDs

        Returns:
            List of created associations
        """
        associations = [
            self.model(listing_id=listing_id, mediator_id=mediator_id)
            for mediator_id in mediator_ids
        ]

        self.db.add_all(associations)
        await self.db.flush()

        return associations

    async def delete_by_listing(self, listing_id: int) -> None:
        """Delete all mediator associations for a listing."""
        await self.db.execute(
            delete(self.model)
            .where(self.model.listing_id == listing_id)
        )

    async def update_associations(
        self,
        listing_id: int,
        mediator_ids: List[int]
    ) -> List[ListingMediator]:
        """
        Replace all mediator associations for a listing.

        Args:
            listing_id: Listing ID
            mediator_ids: New list of mediator IDs

        Returns:
            List of created associations
        """
        # Delete existing associations
        await self.delete_by_listing(listing_id)

        # Create new associations
        return await self.create_associations(listing_id, mediator_ids)

    async def mediator_can_meditate(
        self,
        listing_id: int,
        mediator_id: int
    ) -> bool:
        """
        Check if a mediator is allowed to mediate a listing.

        Args:
            listing_id: Listing ID
            mediator_id: Mediator ID

        Returns:
            True if mediator can mediate, False otherwise
        """
        result = await self.db.execute(
            select(self.model)
            .where(
                self.model.listing_id == listing_id,
                self.model.mediator_id == mediator_id
            )
        )
        return result.scalar_one_or_none() is not None
