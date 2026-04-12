"""
Account browsing API routes.

Handles account discovery, browsing, and retrieval of account details.
Provides endpoints for searching/filtering available game accounts
and finding similar accounts.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.account import (
    AccountDetailResponse,
    AccountsBrowseResponse,
    SimilarAccountsResponse,
)
from app.schemas.common import APIResponse
from app.services.buy import BuyService

router = APIRouter(prefix="/accounts", tags=["Account Browsing"])


@router.get(
    "",
    response_model=APIResponse[AccountsBrowseResponse],
    summary="Browse available accounts",
    description="Search and filter available game accounts with pagination",
)
async def browse_accounts(
    game: Optional[str] = Query(None, description="Filter by game name"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    level: Optional[str] = Query(None, description="Filter by rank/level"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    sort: str = Query("newest", description="Sort: newest, price_asc, price_desc, rating"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AccountsBrowseResponse]:
    """
    Browse available game accounts with filtering and sorting.

    Supports filtering by:
    - Game name
    - Price range
    - Rank/level
    - Full-text search

    Sorting options:
    - newest: Latest listings first
    - price_asc: Lowest price first
    - price_desc: Highest price first
    - rating: Highest rated first
    """
    try:
        service = BuyService(db)
        result = await service.browse_accounts(
            game=game,
            price_min=price_min,
            price_max=price_max,
            level=level,
            search=search,
            sort=sort,
            page=page,
            limit=limit,
        )
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to browse accounts: {str(e)}",
        )


@router.get(
    "/{account_id}",
    response_model=APIResponse[AccountDetailResponse],
    summary="Get account details",
    description="Get full details of a specific game account",
)
async def get_account_details(
    account_id: str, db: AsyncSession = Depends(get_db)
) -> APIResponse[AccountDetailResponse]:
    """
    Retrieve detailed information about a specific account.

    Includes:
    - Full account details
    - Seller information
    - All images and features
    - Availability status
    """
    try:
        service = BuyService(db)
        result = await service.get_account_details(account_id)
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account details: {str(e)}",
        )


@router.get(
    "/{account_id}/similar",
    response_model=APIResponse[SimilarAccountsResponse],
    summary="Get similar accounts",
    description="Get similar accounts based on game, price, or rank",
)
async def get_similar_accounts(
    account_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SimilarAccountsResponse]:
    """
    Get accounts similar to the specified account.

    Similarity is based on:
    - Same game
    - Similar price range (±30%)
    - Similar rank (if available)
    """
    try:
        service = BuyService(db)
        result = await service.get_similar_accounts(account_id, limit)
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar accounts: {str(e)}",
        )
