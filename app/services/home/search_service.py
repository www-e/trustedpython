"""Search service for account search functionality."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ValidationError
from app.models.account import Account, AccountFeature, AccountImage
from app.models.user import User, UserProfile
from app.schemas.common import PaginationSchema
from app.schemas.home import AccountTier, SearchAccountCard, SearchFilters, SearchResponse
from app.services.cache_service import CacheService


class SearchService:
    """Service for account search and filtering business logic."""

    def __init__(self, db: AsyncSession, cache_service: Optional[CacheService] = None):
        """
        Initialize SearchService.

        Args:
            db: Async database session
            cache_service: Optional cache service for caching search results
        """
        self.db = db
        self.cache = cache_service or CacheService()

    async def search_accounts(
        self,
        query: str,
        game: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "relevance",
        page: int = 1,
        limit: int = 20,
    ) -> SearchResponse:
        """
        Search accounts with filters.

        Args:
            query: Search query
            game: Optional game filter
            price_min: Optional minimum price
            price_max: Optional maximum price
            sort: Sort order (relevance, newest, price_asc, price_desc, rating)
            page: Page number
            limit: Items per page

        Returns:
            SearchResponse: Search results with filters

        Raises:
            ValidationError: If search query is too short
        """
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")

        query = query.strip()

        # Build base query
        base_query = (
            select(Account)
            .options(selectinload(Account.images), selectinload(Account.features))
            .where(Account.status == "active")
        )

        # Apply text search
        search_pattern = f"%{query}%"
        base_query = base_query.where(
            or_(
                Account.title.ilike(search_pattern),
                Account.game.ilike(search_pattern),
                Account.description.ilike(search_pattern),
                Account.rank.ilike(search_pattern),
            )
        )

        # Apply filters
        if game:
            base_query = base_query.where(Account.game.ilike(f"%{game}%"))

        if price_min is not None:
            base_query = base_query.where(Account.price >= price_min)

        if price_max is not None:
            base_query = base_query.where(Account.price <= price_max)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if sort == "newest":
            base_query = base_query.order_by(desc(Account.created_at))
        elif sort == "price_asc":
            base_query = base_query.order_by(asc(Account.price))
        elif sort == "price_desc":
            base_query = base_query.order_by(desc(Account.price))
        elif sort == "rating":
            # Sort by views as proxy for popularity (would need reviews table for true rating)
            base_query = base_query.order_by(desc(Account.views_count))
        else:  # relevance
            base_query = base_query.order_by(desc(Account.is_featured), desc(Account.created_at))

        # Apply pagination
        offset = (page - 1) * limit
        base_query = base_query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(base_query)
        accounts = result.scalars().all()

        # Build response with highlights
        search_accounts = []
        for account in accounts:
            # Generate highlights
            highlights = self._generate_search_highlights(account, query)

            # Get first image
            image_url = ""
            if account.images:
                image_url = account.images[0].url

            # Get seller info
            seller_result = await self.db.execute(select(User).where(User.id == account.seller_id))
            seller = seller_result.scalar_one_or_none()

            search_account = SearchAccountCard(
                id=str(account.id),
                title=account.title,
                game=account.game,
                price=float(account.price),
                currency=account.currency,
                image_url=image_url,
                rating=4.5,  # Default rating (would come from reviews table)
                reviews=0,  # Would come from reviews table
                is_premium=account.is_featured,
                tier=AccountTier.GOLD if account.is_featured else None,
                seller_name=seller.username if seller else "Unknown",
                rank=account.rank,
                highlights=highlights,
            )
            search_accounts.append(search_account)

        # Build filters metadata
        filters = await self._get_search_filters()

        # Build pagination
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return SearchResponse(
            query=query,
            total_results=total,
            accounts=search_accounts,
            filters=filters,
            pagination=pagination.model_dump(),
        )

    async def _get_search_filters(self) -> SearchFilters:
        """
        Get available search filters.

        Returns:
            SearchFilters: Available games and price range for filtering
        """
        # Get available games
        games_result = await self.db.execute(
            select(Account.game).where(Account.status == "active").distinct().order_by(Account.game)
        )
        available_games = [game[0] for game in games_result.all()]

        # Get price range
        price_result = await self.db.execute(
            select(
                func.min(Account.price).label("min_price"),
                func.max(Account.price).label("max_price"),
            ).where(Account.status == "active")
        )
        price_data = price_result.first()

        price_range = {
            "min": float(price_data[0]) if price_data and price_data[0] else 0,
            "max": float(price_data[1]) if price_data and price_data[1] else 10000,
        }

        return SearchFilters(available_games=available_games, price_range=price_range)

    def _generate_search_highlights(self, account: Account, query: str) -> List[str]:
        """
        Generate search highlight snippets.

        Args:
            account: Account to generate highlights for
            query: Search query string

        Returns:
            List[str]: List of highlight snippets (max 3)
        """
        highlights = []
        query_lower = query.lower()

        # Check title
        if query_lower in account.title.lower():
            highlights.append(f"Matched in title: {account.title}")

        # Check game
        if query_lower in account.game.lower():
            highlights.append(f"Game: {account.game}")

        # Check rank
        if account.rank and query_lower in account.rank.lower():
            highlights.append(f"Rank: {account.rank}")

        # Check description (truncate if too long)
        if account.description:
            desc_lower = account.description.lower()
            if query_lower in desc_lower:
                # Find the context around the match
                start_idx = desc_lower.find(query_lower)
                context_start = max(0, start_idx - 30)
                context_end = min(len(account.description), start_idx + len(query) + 30)
                snippet = account.description[context_start:context_end]
                if context_start > 0:
                    snippet = "..." + snippet
                if context_end < len(account.description):
                    snippet = snippet + "..."
                highlights.append(f"Description: {snippet}")

        return highlights[:3]  # Max 3 highlights per result
