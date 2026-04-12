"""Home feed service - focused on feed and featured accounts functionality."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.models.account import Account, AccountFeature, AccountImage
from app.models.content import Category, FAQItem, Game, PromoBanner
from app.models.user import User, UserProfile
from app.schemas.common import PaginationSchema
from app.schemas.home import (
    AccountCard,
    AccountTier,
    CategoriesResponse,
    CategoryItem,
    CategoryResponse,
    FAQItemResponse,
    FAQResponse,
    FeaturedAccountCard,
    FeaturedAccountsResponse,
    FeaturedSellerInfo,
    GameAccountCard,
    GameAccountSeller,
    GameAccountsResponse,
    GameInfo,
    GameResponse,
    GamesResponse,
    HomeFeedResponse,
    PromoBannerResponse,
    PromoBannersResponse,
    SearchAccountCard,
    SearchFilters,
    SearchResponse,
)
from app.services.cache_service import CacheService


class HomeFeedService:
    """
    Service for home feed and featured accounts functionality.

    This service is focused on:
    - Main home feed with mixed content
    - Featured/premium accounts
    - Category summaries
    - Account filtering and pagination

    The service provides caching for frequently accessed data and
    supports filtering by category, game, and other criteria.
    """

    def __init__(self, db: AsyncSession, cache_service: Optional[CacheService] = None):
        """
        Initialize HomeFeedService.

        Args:
            db: Async database session
            cache_service: Optional cache service instance (creates default if not provided)
        """
        self.db = db
        self.cache = cache_service or CacheService()

    async def get_home_feed(
        self,
        category: Optional[str] = None,
        game: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> HomeFeedResponse:
        """
        Get main home feed with mixed content.

        This method aggregates:
        - Featured accounts (cached separately)
        - Regular accounts with optional filters
        - Category summaries
        - Pagination metadata

        Args:
            category: Optional category filter for accounts
            game: Optional game filter for accounts
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            HomeFeedResponse: Complete home feed with featured accounts,
                            regular accounts, categories, and pagination

        Example:
            >>> service = HomeFeedService(db)
            >>> feed = await service.get_home_feed(game="Valorant", page=1, limit=20)
            >>> print(feed.featured_accounts)  # List of featured accounts
            >>> print(feed.accounts)  # List of regular accounts
            >>> print(feed.pagination)  # Pagination metadata
        """
        # Get featured accounts (cached separately)
        featured_accounts = await self._get_featured_accounts_internal(limit=5)

        # Get regular accounts with filters
        accounts, total = await self._get_accounts_filtered(
            category=category, game=game, page=page, limit=limit
        )

        # Get categories summary
        categories = await self._get_categories_summary()

        # Build pagination
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return HomeFeedResponse(
            featured_accounts=featured_accounts,
            accounts=accounts,
            categories=categories,
            pagination=pagination.model_dump(),
        )

    async def get_featured_accounts(self, limit: int = 10) -> FeaturedAccountsResponse:
        """
        Get featured/premium accounts.

        Featured accounts are those marked as is_featured=True in the database.
        Results are cached for 5 minutes to reduce database load.

        Args:
            limit: Number of accounts to return (max 20)

        Returns:
            FeaturedAccountsResponse: List of featured accounts with seller info

        Raises:
            ValueError: If limit is not between 1 and 20

        Example:
            >>> service = HomeFeedService(db)
            >>> featured = await service.get_featured_accounts(limit=10)
            >>> for account in featured.accounts:
            ...     print(f"{account.title} - ${account.price}")
        """
        # Validate limit
        limit = min(max(1, limit), 20)

        # Try cache first
        cached = await self.cache.get_cached_featured_accounts()
        if cached:
            # Convert cached dicts back to schema objects
            accounts = [FeaturedAccountCard(**acc) for acc in cached[:limit]]
            return FeaturedAccountsResponse(accounts=accounts)

        # Fetch from database
        accounts = await self._get_featured_accounts_internal(limit=limit)

        # Cache the results
        accounts_dict = [acc.model_dump() for acc in accounts]
        await self.cache.cache_featured_accounts(accounts_dict)

        return FeaturedAccountsResponse(accounts=accounts)

    async def get_categories(self) -> CategoriesResponse:
        """
        Get all available categories.

        Categories are ordered by listing count (most popular first).
        Results are cached for 1 hour.

        Returns:
            CategoriesResponse: List of all active categories

        Example:
            >>> service = HomeFeedService(db)
            >>> categories = await service.get_categories()
            >>> for cat in categories.categories:
            ...     print(f"{cat.name}: {cat.account_count} listings")
        """
        # Try cache first
        cached = await self.cache.get_cached_categories()
        if cached:
            cached_categories = [CategoryResponse(**cat) for cat in cached]
            return CategoriesResponse(categories=cached_categories)

        # Fetch from database
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.listing_count.desc())
        )
        categories: Sequence[Category] = result.scalars().all()

        category_responses: list[CategoryResponse] = []
        for cat in categories:
            category_responses.append(
                CategoryResponse(
                    id=str(cat.id),
                    name=cat.name,
                    slug=cat.slug,
                    icon=cat.icon,
                    description=cat.description,
                    account_count=int(cat.listing_count),
                    is_active=cat.is_active,
                )
            )

        # Cache the results
        categories_dict = [cat.model_dump() for cat in category_responses]
        await self.cache.cache_categories(categories_dict)

        return CategoriesResponse(categories=category_responses)

    async def get_promo_banners(self) -> PromoBannersResponse:
        """
        Get active promotional banners.

        Only returns banners that:
        - Are marked as active
        - Have start_date <= today
        - Have end_date >= today (or no end_date)

        Ordered by priority (highest first) and creation date (newest first).
        Results are cached for 15 minutes.

        Returns:
            PromoBannersResponse: List of active promo banners

        Example:
            >>> service = HomeFeedService(db)
            >>> banners = await service.get_promo_banners()
            >>> for banner in banners.banners:
            ...     print(f"{banner.title}: {banner.action_url}")
        """
        # Try cache first
        cached = await self.cache.get_cached_promo_banners()
        if cached:
            cached_banners = [PromoBannerResponse(**banner) for banner in cached]
            return PromoBannersResponse(banners=cached_banners)

        # Fetch from database
        today = date.today()

        result = await self.db.execute(
            select(PromoBanner)
            .where(
                and_(
                    PromoBanner.is_active == True,
                    PromoBanner.start_date <= today,
                    or_(PromoBanner.end_date.is_(None), PromoBanner.end_date >= today),
                )
            )
            .order_by(PromoBanner.priority.desc(), PromoBanner.created_at.desc())
        )
        banners: Sequence[PromoBanner] = result.scalars().all()

        banner_responses: list[PromoBannerResponse] = []
        for banner in banners:
            banner_responses.append(
                PromoBannerResponse(
                    id=str(banner.id),
                    title=banner.title,
                    subtitle=banner.subtitle,
                    image_url=banner.image_url,
                    action_url=banner.action_url,
                    action_text=banner.action_text,
                    priority=banner.priority,
                    is_active=banner.is_active,
                    start_date=banner.start_date,
                    end_date=banner.end_date,
                )
            )

        # Cache the results
        banners_dict = [banner.model_dump() for banner in banner_responses]
        await self.cache.cache_promo_banners(banners_dict)

        return PromoBannersResponse(banners=banner_responses)

    async def get_faq(self) -> FAQResponse:
        """
        Get FAQ items.

        Returns active FAQ items ordered by display_order and creation date.
        Results are cached for 1 hour.

        Returns:
            FAQResponse: List of FAQ items grouped by category

        Example:
            >>> service = HomeFeedService(db)
            >>> faq = await service.get_faq()
            >>> for item in faq.faq_items:
            ...     print(f"[{item.category}] {item.question}")
        """
        # Try cache first
        cached = await self.cache.get_cached_faq()
        if cached:
            cached_faq_items = [FAQItemResponse(**item) for item in cached]
            return FAQResponse(faq_items=cached_faq_items)

        # Fetch from database
        result = await self.db.execute(
            select(FAQItem)
            .where(FAQItem.is_active == True)
            .order_by(FAQItem.display_order.asc(), FAQItem.created_at.asc())
        )
        faq_items: Sequence[FAQItem] = result.scalars().all()

        faq_responses: list[FAQItemResponse] = []
        for item in faq_items:
            faq_responses.append(
                FAQItemResponse(
                    id=str(item.id),
                    question=item.question,
                    answer=item.answer,
                    category=item.category,
                    order=item.display_order,
                )
            )

        # Cache the results
        faq_dict = [item.model_dump() for item in faq_responses]
        await self.cache.cache_faq(faq_dict)

        return FAQResponse(faq_items=faq_responses)

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

        Searches across account title, game, description, and rank.
        Supports filtering by game and price range.
        Supports multiple sort options.

        Args:
            query: Search query (minimum 2 characters)
            game: Optional game filter
            price_min: Optional minimum price
            price_max: Optional maximum price
            sort: Sort order (relevance, newest, price_asc, price_desc, rating)
            page: Page number
            limit: Items per page

        Returns:
            SearchResponse: Search results with filters and highlights

        Raises:
            ValidationError: If query is less than 2 characters

        Example:
            >>> service = HomeFeedService(db)
            >>> results = await service.search_accounts(
            ...     query="Valorant",
            ...     game="Valorant",
            ...     price_min=50,
            ...     price_max=200,
            ...     sort="price_asc"
            ... )
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

    async def get_games(self, sort: str = "name", limit: int = 50) -> GamesResponse:
        """
        Get all supported games.

        Args:
            sort: Sort order (name, popularity, newest)
            limit: Maximum number of games to return (max 100)

        Returns:
            GamesResponse: List of games

        Example:
            >>> service = HomeFeedService(db)
            >>> games = await service.get_games(sort="popularity", limit=20)
            >>> for game in games.games:
            ...     print(f"{game.name}: {game.active_listings} listings")
        """
        limit = min(max(1, limit), 100)

        # Try cache first
        cached = await self.cache.get_cached_games(sort=sort)
        if cached:
            cached_games = [GameResponse(**game) for game in cached[:limit]]
            return GamesResponse(games=cached_games)

        # Fetch from database
        query = select(Game).where(Game.is_active == True)

        # Apply sorting
        if sort == "popularity":
            query = query.order_by(desc(Game.is_popular), desc(Game.active_listings))
        elif sort == "newest":
            query = query.order_by(desc(Game.created_at))
        else:  # name
            query = query.order_by(Game.name.asc())

        query = query.limit(limit)

        result = await self.db.execute(query)
        games: Sequence[Game] = result.scalars().all()

        game_responses: list[GameResponse] = []
        for game in games:
            game_responses.append(
                GameResponse(
                    id=str(game.id),
                    name=game.name,
                    slug=game.slug,
                    icon_url=game.icon_url,
                    banner_url=game.banner_url,
                    description=game.description,
                    active_listings=game.active_listings,
                    avg_price=float(game.avg_price) if game.avg_price else None,
                    is_popular=game.is_popular,
                    is_trending=game.is_trending,
                )
            )

        # Cache the results
        games_dict = [game.model_dump() for game in game_responses]
        await self.cache.cache_games(games_dict, sort=sort)

        return GamesResponse(games=game_responses)

    async def get_game_accounts(
        self, game_id: UUID, sort: str = "newest", page: int = 1, limit: int = 20
    ) -> GameAccountsResponse:
        """
        Get accounts for a specific game.

        Args:
            game_id: Game ID
            sort: Sort order (newest, price_asc, price_desc, rating)
            page: Page number
            limit: Items per page

        Returns:
            GameAccountsResponse: Game info and accounts

        Raises:
            NotFoundError: If game with given ID doesn't exist

        Example:
            >>> from uuid import UUID
            >>> service = HomeFeedService(db)
            >>> result = await service.get_game_accounts(
            ...     game_id=UUID("12345678-1234-5678-1234-567812345678"),
            ...     sort="price_asc"
            ... )
            >>> print(f"Game: {result.game.name}")
            >>> print(f"Accounts: {len(result.accounts)}")
        """
        # Get game info
        game_result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = game_result.scalar_one_or_none()

        if not game:
            raise NotFoundError(f"Game with ID {game_id} not found")

        # Build game info
        game_info = GameInfo(id=str(game.id), name=game.name, icon_url=game.icon_url)

        # Build accounts query
        query = (
            select(Account)
            .options(selectinload(Account.images), selectinload(Account.features))
            .where(and_(Account.status == "active", Account.game == game.name))
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if sort == "price_asc":
            query = query.order_by(asc(Account.price))
        elif sort == "price_desc":
            query = query.order_by(desc(Account.price))
        elif sort == "rating":
            query = query.order_by(desc(Account.views_count))
        else:  # newest
            query = query.order_by(desc(Account.created_at))

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        accounts = result.scalars().all()

        # Build account cards
        account_cards = []
        for account in accounts:
            # Get first image
            image_url = ""
            if account.images:
                image_url = account.images[0].url

            # Get seller info
            seller_result = await self.db.execute(
                select(User, UserProfile)
                .join(UserProfile, User.id == UserProfile.user_id)
                .where(User.id == account.seller_id)
            )
            seller_data = seller_result.first()

            seller_info = None
            if seller_data:
                seller, profile = seller_data
                seller_info = GameAccountSeller(
                    username=seller.username, avatar_url=profile.avatar_url
                )

            account_card = GameAccountCard(
                id=str(account.id),
                title=account.title,
                game=account.game,
                price=float(account.price),
                currency=account.currency,
                image_url=image_url,
                rating=4.5,  # Default rating
                reviews=0,  # Would come from reviews table
                is_premium=account.is_featured,
                tier=AccountTier.GOLD if account.is_featured else None,
                seller_name=seller_info.username if seller_info else None,
                rank=account.rank,
                seller=seller_info,
            )
            account_cards.append(account_card)

        # Build pagination
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return GameAccountsResponse(
            game=game_info, accounts=account_cards, pagination=pagination.model_dump()
        )

    # Private helper methods

    async def _get_featured_accounts_internal(self, limit: int = 10) -> List[FeaturedAccountCard]:
        """
        Get featured accounts with seller info.

        Internal method that fetches featured accounts from the database.
        Accounts are ordered by verification status and creation date.

        Args:
            limit: Maximum number of accounts to return

        Returns:
            List of FeaturedAccountCard objects with complete seller information
        """
        result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.images), selectinload(Account.features))
            .where(and_(Account.status == "active", Account.is_featured == True))
            .order_by(desc(Account.is_verified), desc(Account.created_at))
            .limit(limit)
        )
        accounts = result.scalars().all()

        featured_accounts = []
        for account in accounts:
            # Get first image
            image_url = ""
            if account.images:
                image_url = account.images[0].url

            # Get seller info
            seller_result = await self.db.execute(
                select(User, UserProfile)
                .join(UserProfile, User.id == UserProfile.user_id)
                .where(User.id == account.seller_id)
            )
            seller_data = seller_result.first()

            seller_info = None
            if seller_data:
                seller, profile = seller_data
                seller_info = FeaturedSellerInfo(
                    username=seller.username,
                    avatar_url=profile.avatar_url,
                    rating=4.8,  # Would come from seller aggregation
                )

            featured_account = FeaturedAccountCard(
                id=str(account.id),
                title=account.title,
                game=account.game,
                price=float(account.price),
                currency=account.currency,
                image_url=image_url,
                rating=4.5,  # Default rating
                reviews=0,  # Would come from reviews table
                is_premium=account.is_featured,
                tier=AccountTier.GOLD,
                seller_name=seller_info.username if seller_info else None,
                rank=account.rank,
                seller=seller_info,
            )
            featured_accounts.append(featured_account)

        return featured_accounts

    async def _get_accounts_filtered(
        self,
        category: Optional[str] = None,
        game: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[AccountCard], int]:
        """
        Get filtered accounts list with total count.

        Internal method that applies filters and returns accounts with pagination.

        Args:
            category: Optional category filter
            game: Optional game filter
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (list of AccountCard objects, total count)
        """
        query = (
            select(Account)
            .options(selectinload(Account.images), selectinload(Account.features))
            .where(Account.status == "active")
        )

        # Apply filters
        if category:
            # Would join with categories table
            pass

        if game:
            query = query.where(Account.game.ilike(f"%{game}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(Account.created_at)).offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        accounts = result.scalars().all()

        # Build account cards
        account_cards = []
        for account in accounts:
            # Get first image
            image_url = ""
            if account.images:
                image_url = account.images[0].url

            # Get seller name
            seller_result = await self.db.execute(select(User).where(User.id == account.seller_id))
            seller = seller_result.scalar_one_or_none()

            account_card = AccountCard(
                id=str(account.id),
                title=account.title,
                game=account.game,
                price=float(account.price),
                currency=account.currency,
                image_url=image_url,
                rating=4.5,  # Default rating
                reviews=0,  # Would come from reviews table
                is_premium=account.is_featured,
                tier=AccountTier.GOLD if account.is_featured else None,
                seller_name=seller.username if seller else "Unknown",
                rank=account.rank,
            )
            account_cards.append(account_card)

        return account_cards, total

    async def _get_categories_summary(self) -> List[CategoryItem]:
        """
        Get categories summary for home feed.

        Returns top 10 categories by listing count.
        Used to populate the categories section of the home feed.

        Returns:
            List of CategoryItem objects with id, name, icon, and count
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.listing_count.desc())
            .limit(10)
        )
        categories = result.scalars().all()

        return [
            CategoryItem(id=str(cat.id), name=cat.name, icon=cat.icon, count=cat.listing_count)
            for cat in categories
        ]

    async def _get_search_filters(self) -> SearchFilters:
        """
        Get available search filters.

        Returns metadata about available filters including:
        - List of all games with active listings
        - Price range (min and max prices)

        Returns:
            SearchFilters object with available games and price range
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

        Creates contextual snippets showing where the search query matches
        in the account data. Returns up to 3 highlights per result.

        Args:
            account: Account object to search in
            query: Search query string

        Returns:
            List of highlight strings (max 3)
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
