"""Exclusive Card service - business logic layer."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exclusive_card import ExclusiveCard
from app.repositories.exclusive_card import ExclusiveCardRepository
from app.schemas.exclusive_card import ExclusiveCardCreate, ExclusiveCardUpdate
from app.exceptions import NotFoundError, ValidationError


class ExclusiveCardService:
    """Service for exclusive card business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize exclusive card service.

        Args:
            db: Database session
        """
        self.db = db
        self.card_repo = ExclusiveCardRepository(db)

    async def get_active_cards(self) -> List[ExclusiveCard]:
        """
        Get all active exclusive cards for public display.

        Returns:
            List of active, non-expired cards ordered by display order
        """
        return await self.card_repo.get_active_cards()

    async def get_all_cards(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExclusiveCard]:
        """
        Get all exclusive cards (admin view).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of all cards ordered by display order
        """
        return await self.card_repo.get_all_ordered(skip=skip, limit=limit)

    async def get_card(self, card_id: int) -> ExclusiveCard:
        """
        Get a specific exclusive card by ID.

        Args:
            card_id: Card ID

        Returns:
            Exclusive card

        Raises:
            NotFoundError: If card doesn't exist
        """
        card = await self.card_repo.get(card_id)
        if not card:
            raise NotFoundError(f"Exclusive card with ID {card_id} not found")
        return card

    async def create_card(self, card_data: ExclusiveCardCreate) -> ExclusiveCard:
        """
        Create a new exclusive card.

        Args:
            card_data: Card creation data

        Returns:
            Created exclusive card
        """
        # Convert Pydantic model to dict
        card_dict = card_data.model_dump()

        # Create card
        card = await self.card_repo.create(**card_dict)
        await self.db.commit()
        await self.db.refresh(card)

        return card

    async def update_card(
        self,
        card_id: int,
        card_data: ExclusiveCardUpdate
    ) -> ExclusiveCard:
        """
        Update an existing exclusive card.

        Args:
            card_id: Card ID
            card_data: Card update data

        Returns:
            Updated exclusive card

        Raises:
            NotFoundError: If card doesn't exist
        """
        # Check if card exists
        await self.get_card(card_id)

        # Filter out None values
        update_data = {k: v for k, v in card_data.model_dump().items() if v is not None}

        # Update card
        updated_card = await self.card_repo.update(card_id, **update_data)
        await self.db.commit()
        await self.db.refresh(updated_card)

        return updated_card

    async def delete_card(self, card_id: int) -> bool:
        """
        Delete an exclusive card.

        Args:
            card_id: Card ID

        Returns:
            True if deleted, False otherwise

        Raises:
            NotFoundError: If card doesn't exist
        """
        # Check if card exists
        await self.get_card(card_id)

        # Delete card
        result = await self.card_repo.delete(card_id)
        await self.db.commit()

        return result
