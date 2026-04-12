"""
Deal management API routes.

Handles deal creation, status updates, and deal retrieval
for the buy flow.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenException
from app.models.deal import Deal
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.deal import (
    CreateDealRequest,
    DealDetailResponse,
    DealResponse,
    DealStatus,
    UpdateDealStatusRequest,
)
from app.services.buy import BuyService

router = APIRouter(prefix="/deals", tags=["Deals"])


# ==================== DEAL ENDPOINTS ====================


@router.post(
    "/",
    response_model=APIResponse[DealResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="Create deal",
    description="Create a new deal (request to buy an account)",
)
async def create_deal(
    request: CreateDealRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DealResponse]:
    """
    Create a new deal to purchase an account.

    This will:
    - Create a deal with PENDING status
    - Create a chat room with buyer, seller, and mediator
    - Send notifications to all parties

    Rate limiting applies to prevent abuse.
    """
    try:
        service = BuyService(db)
        result = await service.create_deal(
            user_id=str(current_user.id),
            account_id=request.account_id,
            mediator_id=request.mediator_id,
            quantity=request.quantity,
            notes=request.notes,
        )
        return APIResponse.success_response(data=result, message="Deal created successfully")
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deal: {str(e)}",
        )


@router.get(
    "/{deal_id}",
    response_model=APIResponse[DealDetailResponse],
    summary="Get deal details",
    description="Get details of a specific deal",
)
async def get_deal_details(
    deal_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[DealDetailResponse]:
    """
    Retrieve detailed deal information.

    Only accessible to deal participants (buyer, seller, mediator).

    Includes full account, mediator, buyer, seller details,
    payment information, and chat room reference.
    """
    try:
        service = BuyService(db)
        result = await service.get_deal_details(deal_id=deal_id, user_id=str(current_user.id))
        return APIResponse.success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deal details: {str(e)}",
        )


@router.put(
    "/{deal_id}/status",
    response_model=APIResponse[DealResponse],
    summary="Update deal status",
    description="Update deal status (mediator action)",
)
async def update_deal_status(
    deal_id: str,
    request: UpdateDealStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DealResponse]:
    """
    Update deal status (mediator only).

    Allowed status transitions:
    - pending → awaiting_payment
    - awaiting_payment → payment_submitted
    - payment_submitted → verified
    - verified → completed
    - Any status → cancelled/disputed (with reason)

    Notes are optional but recommended for status changes.
    """
    try:
        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()
        if not deal:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Deal not found"
            )
        if deal.mediator_id != current_user.id:
            raise ForbiddenException("Only the deal mediator can update deal status")
        service = BuyService(db)
        result = await service.update_deal_status(
            deal_id=deal_id, status=request.status, notes=request.notes
        )
        return APIResponse.success_response(data=result, message="Deal status updated successfully")
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update deal status: {str(e)}",
        )


@router.get(
    "/my",
    response_model=APIResponse[dict],
    summary="Get my deals",
    description="Get authenticated user's deals",
)
async def get_my_deals(
    role: Optional[str] = Query(None, description="Filter by role: buyer or seller"),
    status: Optional[DealStatus] = Query(None, description="Filter by deal status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Get deals for the authenticated user.

    Can filter by:
    - role: "buyer" or "seller"
    - status: Any valid DealStatus

    Returns deals where user is either buyer or seller.
    """
    try:
        service = BuyService(db)
        result = await service.get_user_deals(
            user_id=str(current_user.id), role=role, status=status, page=page, limit=limit
        )
        return APIResponse.success_response(data=result)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user deals: {str(e)}",
        )
