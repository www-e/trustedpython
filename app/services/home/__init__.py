"""
Home services package.

Provides specialized services for home feed, content discovery,
search functionality, and game browsing.

Usage:
    # Direct import (recommended for new code):
    from app.services.home import HomeFeedService, ContentService, SearchService

    # Facade import (for backward compatibility):
    from app.services.home import HomeService
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cache_service import CacheService
from app.services.home.content_service import ContentService
from app.services.home.feed_service import HomeFeedService
from app.services.home.search_service import SearchService

__all__ = [
    "HomeFeedService",
    "ContentService",
    "SearchService",
    "HomeService",  # Facade for backward compatibility
]


# Backward compatibility facade
class HomeService:
    """
    Facade for backward compatibility with legacy HomeService.

    This class provides the same interface as the original monolithic
    HomeService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: AsyncSession, cache_service: CacheService | None = None) -> None:
        """
        Initialize facade with database session and optional cache service.

        Args:
            db: Database session
            cache_service: Optional cache service instance
        """
        self.db = db
        self.cache = cache_service or CacheService()
        self._feed: HomeFeedService | None = None
        self._content: ContentService | None = None
        self._search: SearchService | None = None

    @property
    def feed(self) -> HomeFeedService:
        """Get home feed service instance."""
        if self._feed is None:
            self._feed = HomeFeedService(self.db, self.cache)
        return self._feed

    @property
    def content(self) -> ContentService:
        """Get content discovery service instance."""
        if self._content is None:
            self._content = ContentService(self.db, self.cache)
        return self._content

    @property
    def search(self) -> SearchService:
        """Get search service instance."""
        if self._search is None:
            self._search = SearchService(self.db, self.cache)
        return self._search

    # Home feed methods - delegate to feed service
    async def get_home_feed(
        self,
        category: str | None = None,
        game: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """
        Get main home feed with mixed content.

        Args:
            category: Optional category filter
            game: Optional game filter
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            HomeFeedResponse: Complete home feed with featured accounts, accounts, categories
        """
        return await self.feed.get_home_feed(category, game, page, limit)

    async def get_featured_accounts(self, limit: int = 10) -> Any:
        """
        Get featured/premium accounts.

        Args:
            limit: Number of accounts to return (max 20)

        Returns:
            FeaturedAccountsResponse: Featured accounts with seller info
        """
        return await self.feed.get_featured_accounts(limit)

    # Content discovery methods - delegate to content service
    async def get_categories(self) -> Any:
        """
        Get all active categories with account counts.

        Returns:
            CategoriesResponse: List of categories with metadata
        """
        return await self.content.get_categories()

    async def get_promo_banners(self) -> Any:
        """
        Get active promotional banners.

        Returns:
            PromoBannersResponse: List of active promo banners
        """
        return await self.content.get_promo_banners()

    async def get_faq(self) -> Any:
        """
        Get FAQ items organized by category.

        Returns:
            FAQResponse: FAQ items grouped by category
        """
        return await self.content.get_faq()

    # Search methods - delegate to search service
    async def search_accounts(
        self,
        query: str,
        category: str | None = None,
        game: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        level: str | None = None,
        sort: str = "relevance",
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """
        Search accounts with filters.

        Args:
            query: Search query string
            category: Optional category filter
            game: Optional game filter
            price_min: Optional minimum price
            price_max: Optional maximum price
            level: Optional account level filter
            sort: Sort option (relevance, newest, price_low, price_high)
            page: Page number
            limit: Results per page

        Returns:
            SearchResponse: Search results with filters and pagination
        """
        return await self.search.search_accounts(
            query=query,
            game=game,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
            page=page,
            limit=limit,
        )

    # Game methods - delegate to feed service (has get_games and get_game_accounts)
    async def get_games(self, sort: str = "name", limit: int = 50) -> Any:
        """
        Get all games with account counts.

        Args:
            sort: Sort option (name, accounts, newest)
            limit: Maximum games to return

        Returns:
            GamesResponse: List of games with metadata
        """
        return await self.feed.get_games(sort, limit)

    async def get_game_accounts(
        self,
        game_id: UUID,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """
        Get accounts for a specific game.

        Args:
            game_id: Game ID
            sort: Sort option (newest, price_low, price_high, level)
            page: Page number
            limit: Results per page

        Returns:
            GameAccountsResponse: Game info with accounts list
        """
        return await self.feed.get_game_accounts(
            game_id=game_id,
            sort=sort,
            page=page,
            limit=limit,
        )
