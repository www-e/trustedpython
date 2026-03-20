"""Deal repository."""

from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.deal import Deal
from app.models.listing import Listing
from app.models.user import User
from app.repositories.base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    """Repository for Deal model."""

    async def get_by_listing(self, listing_id: int) -> List[Deal]:
        """Get all deals for a listing."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.listing_id == listing_id)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: int,
        as_buyer: bool = False,
        as_seller: bool = False,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Deal]:
        """
        Get deals for a user (as buyer, seller, or both).

        Args:
            user_id: User ID
            as_buyer: Filter where user is buyer
            as_seller: Filter where user is seller
            status: Filter by deal status
            limit: Max results
            offset: Offset for pagination

        Returns:
            List of deals
        """
        query = select(self.model)

        conditions = []
        if as_buyer:
            conditions.append(self.model.buyer_id == user_id)
        if as_seller:
            conditions.append(self.model.seller_id == user_id)
        if not as_buyer and not as_seller:
            # If neither specified, get both
            conditions.append(
                or_(
                    self.model.buyer_id == user_id,
                    self.model.seller_id == user_id
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        if status:
            query = query.where(self.model.status == status)

        query = query.order_by(self.model.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_relations(
        self,
        deal_id: int
    ) -> Optional[Deal]:
        """
        Get deal with all related objects loaded.

        Args:
            deal_id: Deal ID

        Returns:
            Deal with listing, buyer, seller, and mediator loaded
        """
        result = await self.db.execute(
            select(self.model)
            .options(
                selectinload(self.model.listing),
                selectinload(self.model.buyer),
                selectinload(self.model.seller),
                selectinload(self.model.mediator)
            )
            .where(self.model.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def count_by_user(
        self,
        user_id: int,
        as_buyer: bool = False,
        as_seller: bool = False,
        status: Optional[str] = None
    ) -> int:
        """Count deals for a user."""
        from sqlalchemy import func

        query = select(func.count(self.model.id))

        conditions = []
        if as_buyer:
            conditions.append(self.model.buyer_id == user_id)
        if as_seller:
            conditions.append(self.model.seller_id == user_id)
        if not as_buyer and not as_seller:
            conditions.append(
                or_(
                    self.model.buyer_id == user_id,
                    self.model.seller_id == user_id
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        if status:
            query = query.where(self.model.status == status)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_pending_deals(self, limit: int = 100) -> List[Deal]:
        """Get all pending deals awaiting mediator assignment."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.status == 'pending')
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
