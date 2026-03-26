"""User statistics and trade history service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.exceptions import NotFoundError


class UserStatsService:
    """Service for user statistics and trade history."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user stats service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user_stats(self, user_id: int) -> dict:
        """
        Get user statistics.

        Args:
            user_id: User ID

        Returns:
            Dictionary with user statistics

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return {
            "total_deals_as_buyer": user.total_deals_as_buyer,
            "total_deals_as_seller": user.total_deals_as_seller,
            "completed_deals": user.completed_deals,
            "rating": float(user.rating),
        }

    async def get_trade_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> list:
        """
        Get user's trade history (deals as buyer and seller).

        Args:
            user_id: User ID
            limit: Maximum number of deals to return
            offset: Pagination offset

        Returns:
            List of deals with listing info
        """
        from app.repositories.deal import DealRepository

        deal_repo = DealRepository(self.db)
        deals = await deal_repo.get_by_user(
            user_id=user_id,
            as_buyer=False,
            as_seller=False,
            limit=limit,
            offset=offset
        )

        # Format deals for response
        trade_history = []
        for deal in deals:
            # Determine user's role in this deal
            user_role = "buyer" if deal.buyer_id == user_id else "seller"

            trade_history.append({
                "id": deal.id,
                "listing_id": deal.listing_id,
                "listing_title": deal.listing.title if deal.listing else "Unknown Listing",
                "listing_price": float(deal.listing.price) if deal.listing else 0.0,
                "status": deal.status,
                "user_role": user_role,
                "created_at": deal.created_at,
                "updated_at": deal.updated_at,
            })

        return trade_history

    async def get_mediators(
        self,
        min_rating: float = 0.0,
        limit: int = 100,
        offset: int = 0
    ) -> list[User]:
        """
        Get list of available mediators.

        Args:
            min_rating: Minimum rating filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of mediator users
        """
        return await self.user_repo.get_mediators(
            min_rating=min_rating,
            skip=offset,
            limit=limit
        )
