"""Deal API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.models.enums import UserRole, DealStatus
from app.schemas.deal import (
    DealCreate,
    DealUpdate,
    DealResponse,
    DealWithListingResponse,
    DealListResponse,
)
from app.services.deal_service import DealService
from app.exceptions import NotFoundError, ValidationError, ForbiddenError

router = APIRouter()


@router.post("/", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new deal (initiate purchase).

    Buyer initiates a deal to buy a listing.
    Deal will be in 'pending' status awaiting mediator assignment.
    """
    try:
        deal_data = DealCreate(listing_id=listing_id, buyer_id=current_user.id, seller_id=0, price=0)
        deal = await DealService(db).create_deal(listing_id, current_user.id, deal_data)
        return deal
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/my", response_model=List[DealWithListingResponse])
async def get_my_deals(
    as_buyer: bool = False,
    as_seller: bool = False,
    status_filter: DealStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's deals.

    Can filter by role (buyer/seller) and status.
    """
    deals = await DealService(db).get_user_deals(
        user_id=current_user.id,
        as_buyer=as_buyer,
        as_seller=as_seller,
        status=status_filter.value if status_filter else None,
        limit=limit,
        offset=offset,
    )
    return deals


@router.get("/{deal_id}", response_model=DealWithListingResponse)
async def get_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get deal by ID with all relations."""
    try:
        deal = await DealService(db).get_deal(deal_id)

        # Check if user is part of the deal or is admin/mediator
        if (
            current_user.id != deal.buyer_id
            and current_user.id != deal.seller_id
            and current_user.role not in [UserRole.ADMIN, UserRole.MEDIATOR]
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this deal"
            )

        return DealWithListingResponse(
            id=deal.id,
            listing_id=deal.listing_id,
            buyer_id=deal.buyer_id,
            seller_id=deal.seller_id,
            mediator_id=deal.mediator_id,
            price=float(deal.price),
            status=deal.status,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            listing_title=deal.listing.title if deal.listing else None,
            listing_game_type=deal.listing.game_type.value if deal.listing else None,
            seller_username=deal.seller.username if deal.seller else None,
            buyer_username=deal.buyer.username if deal.buyer else None,
            mediator_username=deal.mediator.username if deal.mediator else None,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{deal_id}/status", response_model=DealResponse)
async def update_deal_status(
    deal_id: int,
    status: DealStatus,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MEDIATOR])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update deal status.

    Only admins and mediators can update deal status.
    """
    try:
        deal = await DealService(db).update_deal_status(deal_id, status)
        return deal
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{deal_id}/assign-mediator", response_model=DealResponse)
async def assign_mediator(
    deal_id: int,
    mediator_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MEDIATOR])),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a mediator to a deal.

    Only admins and mediators can assign mediators.
    """
    try:
        deal = await DealService(db).assign_mediator(deal_id, mediator_id)
        return deal
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deal_id}/cancel", response_model=DealResponse)
async def cancel_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a deal.

    Only buyer or seller can cancel their deal.
    """
    try:
        deal = await DealService(db).cancel_deal(deal_id, current_user.id)
        return deal
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/pending", response_model=List[DealResponse])
async def get_pending_deals(
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MEDIATOR])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all pending deals awaiting mediator assignment.

    Only admins and mediators can view pending deals.
    """
    deals = await DealService(db).get_pending_deals(limit=limit)
    return deals
