"""
Account Browsing Service.

Handles account browsing, filtering, and detailed account information retrieval.
"""

import uuid
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.user import User, UserProfile
from app.schemas.account import (
    AccountDetailResponse,
    AccountFeatureSchema,
    AccountFiltersSchema,
    AccountResponse,
    AccountsBrowseResponse,
    PriceRangeSchema,
    SellerInfoSchema,
    SimilarAccountsResponse,
)
from app.schemas.common import PaginationSchema


class AccountBrowsingService:
    """Service for account browsing operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the service.

        Args:
            db: Async database session
        """
        self.db = db

    async def browse_accounts(
        self,
        game: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> AccountsBrowseResponse:
        """
        Browse and filter available accounts.

        Args:
            game: Filter by game name
            price_min: Minimum price
            price_max: Maximum price
            level: Filter by rank/level
            search: Full-text search query
            sort: Sort order (newest, price_asc, price_desc, rating)
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            AccountsBrowseResponse with accounts and filters
        """
        # Build query
        query = select(Account).where(Account.status == "active")

        # Apply filters
        if game:
            query = query.where(Account.game.ilike(f"%{game}%"))
        if price_min is not None:
            query = query.where(Account.price >= price_min)
        if price_max is not None:
            query = query.where(Account.price <= price_max)
        if level:
            query = query.where(Account.rank.ilike(f"%{level}%"))
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Account.title.ilike(search_pattern),
                    Account.description.ilike(search_pattern),
                    Account.game.ilike(search_pattern),
                )
            )

        # Apply sorting
        if sort == "price_asc":
            query = query.order_by(Account.price.asc())
        elif sort == "price_desc":
            query = query.order_by(Account.price.desc())
        elif sort == "rating":
            # Account model has no rating column; fall back to newest
            query = query.order_by(Account.created_at.desc())
        else:  # newest
            query = query.order_by(Account.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query with relationships
        query = query.options(
            selectinload(Account.images),
            selectinload(Account.features),
            selectinload(Account.seller),
        )

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        # Convert to response schemas
        account_responses = []
        for account in accounts:
            seller_profile = account.seller.profile if account.seller else None
            account_responses.append(
                AccountResponse(
                    id=str(account.id),
                    title=account.title,
                    game=account.game,
                    rank=account.rank,
                    price=float(account.price),
                    currency=account.currency or "EGP",
                    seller_id=str(account.seller_id),
                    seller_name=account.seller.username if account.seller else "",
                    seller_avatar=(
                        seller_profile.avatar_url if seller_profile else None
                    ),
                    rating=float(seller_profile.rating) if seller_profile else 0.0,
                    reviews_count=account.views_count or 0,
                    description=account.description or "",
                    images=[img.url for img in account.images],
                    features=[
                        AccountFeatureSchema(icon=f.icon, label=f.label) for f in account.features
                    ],
                    is_verified=account.is_verified,
                    is_featured=account.is_featured,
                    created_at=account.created_at,
                )
            )

        # Get available filters
        filters = await self._get_account_filters()

        # Create pagination
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return AccountsBrowseResponse(
            accounts=account_responses,
            filters=filters,
            pagination={
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
                "total_pages": pagination.total_pages,
            },
        )

    async def get_account_details(self, account_id: str) -> AccountDetailResponse:
        """
        Get detailed account information.

        Args:
            account_id: Account ID

        Returns:
            AccountDetailResponse with full account details

        Raises:
            ValueError: If account not found
        """
        query = select(Account).where(Account.id == uuid.UUID(account_id))
        query = query.options(
            selectinload(Account.images),
            selectinload(Account.features),
            selectinload(Account.seller).selectinload(User.profile),
        )

        result = await self.db.execute(query)
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError("Account not found")

        # Build seller info
        seller_profile = account.seller.profile if account.seller else None
        seller_info = SellerInfoSchema(
            id=str(account.seller.id),
            username=account.seller.username,
            display_name=(
                seller_profile.display_name
                if seller_profile
                else account.seller.username
            ),
            avatar_url=seller_profile.avatar_url if seller_profile else None,
            is_online=False,
            rating=float(seller_profile.rating) if seller_profile else 0.0,
            total_sales=seller_profile.accounts_sold if seller_profile else 0,
            member_since=account.seller.created_at,
        )

        return AccountDetailResponse(
            id=str(account.id),
            title=account.title,
            game=account.game,
            rank=account.rank,
            price=float(account.price),
            currency=account.currency or "EGP",
            seller=seller_info,
            rating=float(seller_profile.rating) if seller_profile else 0.0,
            reviews_count=account.views_count or 0,
            description=account.description or "",
            images=[img.url for img in account.images],
            features=[AccountFeatureSchema(icon=f.icon, label=f.label) for f in account.features],
            is_verified=account.is_verified,
            is_featured=account.is_featured,
            is_available=account.status == "active",
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    async def get_similar_accounts(
        self, account_id: str, limit: int = 10
    ) -> SimilarAccountsResponse:
        """
        Get similar accounts based on game, price, or rank.

        Args:
            account_id: Original account ID
            limit: Maximum number of similar accounts

        Returns:
            SimilarAccountsResponse

        Raises:
            ValueError: If account not found
        """
        # Get original account
        account_query = select(Account).where(Account.id == uuid.UUID(account_id))
        result = await self.db.execute(account_query)
        original_account = result.scalar_one_or_none()

        if not original_account:
            raise ValueError("Account not found")

        # Find similar accounts
        price_range = original_account.price * 0.3  # 30% price variance
        query = select(Account).where(
            and_(
                Account.id != uuid.UUID(account_id),
                Account.status == "active",
                Account.game == original_account.game,
                Account.price >= original_account.price - price_range,
                Account.price <= original_account.price + price_range,
            )
        )

        query = query.options(
            selectinload(Account.images),
            selectinload(Account.features),
            selectinload(Account.seller),
        )

        query = query.limit(limit)
        result = await self.db.execute(query)
        similar_accounts = result.scalars().all()

        # Convert to response
        account_responses = []
        for account in similar_accounts:
            seller_profile = account.seller.profile if account.seller else None
            account_responses.append(
                AccountResponse(
                    id=str(account.id),
                    title=account.title,
                    game=account.game,
                    rank=account.rank,
                    price=float(account.price),
                    currency=account.currency or "EGP",
                    seller_id=str(account.seller_id),
                    seller_name=account.seller.username if account.seller else "",
                    seller_avatar=(
                        seller_profile.avatar_url if seller_profile else None
                    ),
                    rating=float(seller_profile.rating) if seller_profile else 0.0,
                    reviews_count=account.views_count or 0,
                    description=account.description or "",
                    images=[img.url for img in account.images],
                    features=[
                        AccountFeatureSchema(icon=f.icon, label=f.label) for f in account.features
                    ],
                    is_verified=account.is_verified,
                    is_featured=account.is_featured,
                    created_at=account.created_at,
                )
            )

        return SimilarAccountsResponse(accounts=account_responses)

    async def _get_account_filters(self) -> AccountFiltersSchema:
        """
        Get available filters for account browsing.

        Returns:
            AccountFiltersSchema with available filter options
        """
        # Get unique games
        games_query = select(Account.game).distinct().where(Account.status == "active")
        games_result = await self.db.execute(games_query)
        games = [g[0] for g in games_result.all()]

        # Get unique levels/ranks
        levels_query = (
            select(Account.rank)
            .distinct()
            .where(and_(Account.status == "active", Account.rank.isnot(None)))
        )
        levels_result = await self.db.execute(levels_query)
        levels = [l[0] for l in levels_result.all() if l[0]]

        # Default price ranges - can be made configurable via admin panel
        price_ranges = [
            PriceRangeSchema(label="Under $100", min=0, max=100),
            PriceRangeSchema(label="$100 - $300", min=100, max=300),
            PriceRangeSchema(label="$300 - $500", min=300, max=500),
            PriceRangeSchema(label="Over $500", min=500, max=None),
        ]

        return AccountFiltersSchema(
            available_games=games, price_ranges=price_ranges, available_levels=levels
        )
