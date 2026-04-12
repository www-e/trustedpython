"""Home feed business logic service."""

import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional
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


class HomeService:
    """Service for home feed and discovery business logic."""

    def __init__(self, db: AsyncSession, cache_service: Optional[CacheService] = None):
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

        Args:
            category: Optional category filter
            game: Optional game filter
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            HomeFeedResponse: Complete home feed with featured accounts, accounts, categories
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

        Args:
            limit: Number of accounts to return (max 20)

        Returns:
            FeaturedAccountsResponse: List of featured accounts
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

        Returns:
            CategoriesResponse: List of all categories
        """
        # Try cache first
        cached = await self.cache.get_cached_categories()
        if cached:
            categories = [CategoryResponse(**cat) for cat in cached]
            return CategoriesResponse(categories=categories)

        # Fetch from database
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.listing_count.desc())
        )
        db_categories = result.scalars().all()

        category_responses = [
            CategoryResponse(
                id=str(cat.id),
                name=cat.name,
                slug=cat.slug,
                icon=cat.icon,
                description=cat.description,
                account_count=cat.listing_count,
                is_active=cat.is_active,
            )
            for cat in db_categories
        ]

        # Cache the results
        categories_dict = [cat.model_dump() for cat in category_responses]
        await self.cache.cache_categories(categories_dict)

        return CategoriesResponse(categories=category_responses)

    async def get_promo_banners(self) -> PromoBannersResponse:
        """
        Get active promotional banners.

        Returns:
            PromoBannersResponse: List of active promo banners
        """
        # Try cache first
        cached = await self.cache.get_cached_promo_banners()
        if cached:
            banners = [PromoBannerResponse(**banner) for banner in cached]
            return PromoBannersResponse(banners=banners)

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
        db_banners = result.scalars().all()

        banner_responses = [
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
            for banner in db_banners
        ]

        # Cache the results
        banners_dict = [banner.model_dump() for banner in banner_responses]
        await self.cache.cache_promo_banners(banners_dict)

        return PromoBannersResponse(banners=banner_responses)

    async def get_faq(self) -> FAQResponse:
        """
        Get FAQ items.

        Returns:
            FAQResponse: List of FAQ items
        """
        # Try cache first
        cached = await self.cache.get_cached_faq()
        if cached:
            faq_items = [FAQItemResponse(**item) for item in cached]
            return FAQResponse(faq_items=faq_items)

        # Fetch from database
        result = await self.db.execute(
            select(FAQItem)
            .where(FAQItem.is_active == True)
            .order_by(FAQItem.display_order.asc(), FAQItem.created_at.asc())
        )
        db_faq_items = result.scalars().all()

        faq_responses = [
            FAQItemResponse(
                id=str(item.id),
                question=item.question,
                answer=item.answer,
                category=item.category,
                order=item.display_order,
            )
            for item in db_faq_items
        ]

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
            limit: Maximum number of games to return

        Returns:
            GamesResponse: List of games
        """
        limit = min(max(1, limit), 100)

        # Try cache first
        cached = await self.cache.get_cached_games(sort=sort)
        if cached:
            games = [GameResponse(**game) for game in cached[:limit]]
            return GamesResponse(games=games)

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
        db_games = result.scalars().all()

        game_responses = [
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
            for game in db_games
        ]

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
        """Get featured accounts with seller info."""
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
        """Get filtered accounts list with total count."""
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
        """Get categories summary for home feed."""
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
        """Get available search filters."""
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
            "min": float(price_data.min_price) if price_data and price_data.min_price else 0,
            "max": float(price_data.max_price) if price_data and price_data.max_price else 10000,
        }

        return SearchFilters(available_games=available_games, price_range=price_range)

    def _generate_search_highlights(self, account: Account, query: str) -> List[str]:
        """Generate search highlight snippets."""
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
