"""Mediator API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.mediator import MediatorResponse, MediatorListResponse
from app.services.mediator_service import MediatorService
from app.services.user_service import UserService
from app.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.get("/available", response_model=MediatorListResponse)
async def get_available_mediators(
    min_rating: float = Query(0.0, ge=0.0, le=5.0),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of available mediators.

    Anyone can view available mediators.
    Can filter by minimum rating.
    """
    try:
        mediators = await UserService(db).get_mediators(
            min_rating=min_rating,
            limit=limit,
            offset=offset,
        )

        mediator_responses = [
            MediatorResponse(
                id=m.id,
                username=m.username,
                avatar_url=m.avatar_url,
                rating=float(m.rating),
                completed_deals=m.completed_deals,
                is_available=True,
            )
            for m in mediators
        ]

        return MediatorListResponse(
            mediators=mediator_responses,
            total=len(mediator_responses),
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{mediator_id}/stats", response_model=dict)
async def get_mediator_stats(
    mediator_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get mediator statistics."""
    try:
        stats = await MediatorService(db).get_mediator_stats(mediator_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Mediator not found")
        return stats
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{mediator_id}/can-mediate/{listing_id}", response_model=dict)
async def check_can_meditate(
    mediator_id: int,
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if a mediator can mediate a listing.

    Useful for sellers when selecting mediators for their listings.
    """
    can_meditate = await MediatorService(db).can_mediator_meditate_listing(
        listing_id,
        mediator_id
    )

    return {
        "can_meditate": can_meditate,
        "mediator_id": mediator_id,
        "listing_id": listing_id,
    }
