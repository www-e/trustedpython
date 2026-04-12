"""Home feed API routes."""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, paginate, PaginationParams
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.common import APIResponse
from app.schemas.home import (
    CategoriesResponse,
    FAQResponse,
    FeaturedAccountsResponse,
    GameAccountsResponse,
    GamesResponse,
    HomeFeedResponse,
    PromoBannersResponse,
    SearchResponse,
)
from app.services.home_service import HomeService

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.get("/feed", response_model=APIResponse[HomeFeedResponse])
async def get_home_feed(
    category: Optional[str] = Query(None, description="Filter by category"),
    game: Optional[str] = Query(None, description="Filter by game name"),
    pagination: PaginationParams = Depends(paginate),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[HomeFeedResponse]:
    """
    Get main home feed.

    Returns mixed content including featured accounts, regular accounts, and categories.
    All content is public - no authentication required.

    - **category**: Optional category filter
    - **game**: Optional game filter
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    service = HomeService(db)
    feed = await service.get_home_feed(
        category=category, game=game, page=pagination.page, limit=pagination.limit
    )
    return APIResponse.success_response(data=feed)


@router.get("/featured", response_model=APIResponse[FeaturedAccountsResponse])
async def get_featured_accounts(
    limit: int = Query(10, ge=1, le=20, description="Number of accounts (max: 20)"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[FeaturedAccountsResponse]:
    """
    Get featured/premium accounts.

    Returns curated premium accounts with higher quality ratings and verified status.
    All accounts are manually reviewed for quality.
    """
    service = HomeService(db)
    featured = await service.get_featured_accounts(limit=limit)
    return APIResponse.success_response(data=featured)


@router.get("/categories", response_model=APIResponse[CategoriesResponse])
async def get_categories(db: AsyncSession = Depends(get_db)) -> APIResponse[CategoriesResponse]:
    """
    Get all available categories.

    Returns list of categories with account counts.
    Categories are organized by game types and account tiers.
    """
    service = HomeService(db)
    categories = await service.get_categories()
    return APIResponse.success_response(data=categories)


@router.get("/promo", response_model=APIResponse[PromoBannersResponse])
async def get_promo_banners(db: AsyncSession = Depends(get_db)) -> APIResponse[PromoBannersResponse]:
    """
    Get promotional banners.

    Returns active marketing banners for the home screen.
    Banners are filtered by active date range and priority.
    """
    service = HomeService(db)
    banners = await service.get_promo_banners()
    return APIResponse.success_response(data=banners)


@router.get("/faq", response_model=APIResponse[FAQResponse])
async def get_faq(db: AsyncSession = Depends(get_db)) -> APIResponse[FAQResponse]:
    """
    Get FAQ items.

    Returns frequently asked questions and answers.
    Organized by category for easy navigation.
    """
    service = HomeService(db)
    faq = await service.get_faq()
    return APIResponse.success_response(data=faq)


@router.get("/search", response_model=APIResponse[SearchResponse])
@limiter.limit("30/minute")
async def search_accounts(
    request: Request,
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    game: Optional[str] = Query(None, description="Filter by game"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: str = Query(
        "relevance", description="Sort: relevance, newest, price_asc, price_desc, rating"
    ),
    pagination: PaginationParams = Depends(paginate),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SearchResponse]:
    """
    Search accounts with filters.

    Full-text search across account titles, games, descriptions, and ranks.
    Supports filtering by game, price range, and sorting.

    - **q**: Search query (min 2 characters)
    - **game**: Optional game filter
    - **price_min**: Optional minimum price
    - **price_max**: Optional maximum price
    - **sort**: Sort order (relevance, newest, price_asc, price_desc, rating)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Rate limited to 30 requests per minute to prevent scraping.
    """
    try:
        service = HomeService(db)
        results = await service.search_accounts(
            query=q,
            game=game,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
            page=pagination.page,
            limit=pagination.limit,
        )
        return APIResponse.success_response(data=results)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/games", response_model=APIResponse[GamesResponse])
async def get_games(
    sort: str = Query("name", description="Sort: name, popularity, newest"),
    limit: int = Query(50, ge=1, le=100, description="Maximum games to return"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GamesResponse]:
    """
    Get all supported games.

    Returns list of games with metadata including active listings, average price, and popularity indicators.
    """
    service = HomeService(db)
    games = await service.get_games(sort=sort, limit=limit)
    return APIResponse.success_response(data=games)


@router.get("/games/{gameId}/accounts", response_model=APIResponse[GameAccountsResponse])
async def get_game_accounts(
    gameId: UUID,
    sort: str = Query("newest", description="Sort: newest, price_asc, price_desc, rating"),
    pagination: PaginationParams = Depends(paginate),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GameAccountsResponse]:
    """
    Get accounts for a specific game.

    Returns paginated list of accounts for the specified game.
    Includes game information and seller details.

    - **gameId**: Game ID (UUID)
    - **sort**: Sort order (newest, price_asc, price_desc, rating)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    try:
        service = HomeService(db)
        game_accounts = await service.get_game_accounts(
            game_id=gameId, sort=sort, page=pagination["page"], limit=pagination["limit"]
        )
        return APIResponse.success_response(data=game_accounts)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
