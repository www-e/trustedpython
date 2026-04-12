"""
Mediator API routes.

Handles mediator listing, details, and reviews for the buy flow.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.mediator import MediatorDetailResponse, MediatorReviewsResponse
from app.services.buy import BuyService

router = APIRouter(prefix="/mediators", tags=["Mediators"])


# ==================== MEDIATOR ENDPOINTS ====================


@router.get(
    "/",
    response_model=APIResponse[dict],
    summary="List mediators",
    description="Get available mediators with filtering and sorting",
)
async def list_mediators(
    specialization: Optional[str] = Query(None, description="Filter by game specialization"),
    sort: str = Query("rating", description="Sort: rating, transactions, tier"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    List available mediators for transaction facilitation.

    Supports filtering by game specialization and sorting by:
    - rating: Highest rated first
    - transactions: Most transactions first
    - tier: Highest tier first
    """
    try:
        service = BuyService(db)
        result = await service.list_mediators(
            specialization=specialization, sort=sort, page=page, limit=limit
        )
        return APIResponse.success_response(data=result)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list mediators: {str(e)}",
        )


@router.get(
    "/{mediator_id}",
    response_model=APIResponse[MediatorDetailResponse],
    summary="Get mediator details",
    description="Get full mediator profile with statistics",
)
async def get_mediator_details(
    mediator_id: str, db: AsyncSession = Depends(get_db)
) -> APIResponse[MediatorDetailResponse]:
    """
    Retrieve detailed mediator information.

    Includes:
    - Full profile
    - Statistics (deals, success rate, response time)
    - Badges and achievements
    - Payment methods
    """
    try:
        service = BuyService(db)
        result = await service.get_mediator_details(mediator_id)
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mediator details: {str(e)}",
        )


@router.get(
    "/{mediator_id}/reviews",
    response_model=APIResponse[MediatorReviewsResponse],
    summary="Get mediator reviews",
    description="Get reviews for a specific mediator",
)
async def get_mediator_reviews(
    mediator_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediatorReviewsResponse]:
    """
    Get reviews for a specific mediator.

    Includes reviewer information, ratings, comments,
    and associated deal references.
    """
    try:
        service = BuyService(db)
        result = await service.get_mediator_reviews(mediator_id=mediator_id, page=page, limit=limit)
        return APIResponse.success_response(data=result)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mediator reviews: {str(e)}",
        )
