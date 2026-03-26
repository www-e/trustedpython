"""Exclusive Card repository with data access logic."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_

from app.models.exclusive_card import ExclusiveCard
from app.repositories.base import BaseRepository


class ExclusiveCardRepository(BaseRepository[ExclusiveCard]):
    """Repository for ExclusiveCard model."""

    def __init__(self, db):
        """
        Initialize exclusive card repository.

        Args:
            db: Database session
        """
        super().__init__(ExclusiveCard, db)

    async def get_active_cards(self) -> List[ExclusiveCard]:
        """
        Get all active exclusive cards that are currently visible.

        Returns:
            List of active cards ordered by order field, excluding expired cards
        """
        now = datetime.utcnow()

        result = await self.db.execute(
            select(self.model)
            .where(
                and_(
                    self.model.is_active == True,
                    or_(
                        self.model.display_until is None,
                        self.model.display_until > now
                    )
                )
            )
            .order_by(self.model.order.asc(), self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_ordered(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExclusiveCard]:
        """
        Get all exclusive cards ordered by display order.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of cards ordered by order field
        """
        result = await self.db.execute(
            select(self.model)
            .order_by(self.model.order.asc(), self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
