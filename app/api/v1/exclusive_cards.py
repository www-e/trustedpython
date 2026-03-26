"""Exclusive Card API endpoints (public)."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.services.exclusive_card_service import ExclusiveCardService
from app.schemas.exclusive_card import ExclusiveCardResponse

router = APIRouter()


@router.get(
    "/exclusive-cards",
    response_model=List[ExclusiveCardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active exclusive cards",
    description="Retrieve all active exclusive cards for home screen display"
)
async def get_exclusive_cards(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active exclusive cards.

    Returns active, non-expired cards ordered by display order.
    Used for the home screen exclusive section.
    """
    service = ExclusiveCardService(db)
    cards = await service.get_active_cards()
    return [ExclusiveCardResponse.model_validate(card) for card in cards]
