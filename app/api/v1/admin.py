"""Admin API endpoints for exclusive cards, listings, and categories management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.models.enums import UserRole
from app.services.exclusive_card_service import ExclusiveCardService
from app.services.listing_service import ListingService
from app.services.category_service import CategoryService
from app.schemas.exclusive_card import (
    ExclusiveCardResponse,
    ExclusiveCardCreate,
    ExclusiveCardUpdate
)
from app.schemas.listing import ListingResponse
from app.schemas.category import CategoryResponse

router = APIRouter()


# Exclusive Cards Endpoints
@router.get(
    "/admin/exclusive-cards",
    response_model=List[ExclusiveCardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all exclusive cards (Admin)",
    description="Retrieve all exclusive cards including inactive ones (Admin only)"
)
async def get_all_exclusive_cards(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all exclusive cards (admin view).

    Requires admin role. Returns all cards regardless of active status.
    """
    service = ExclusiveCardService(db)
    cards = await service.get_all_cards(skip=skip, limit=limit)
    return [ExclusiveCardResponse.model_validate(card) for card in cards]


@router.post(
    "/admin/exclusive-cards",
    response_model=ExclusiveCardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create exclusive card (Admin)",
    description="Create a new exclusive card (Admin only)"
)
async def create_exclusive_card(
    card_data: ExclusiveCardCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new exclusive card.

    Requires admin role.
    """
    service = ExclusiveCardService(db)
    card = await service.create_card(card_data)
    return ExclusiveCardResponse.model_validate(card)


@router.put(
    "/admin/exclusive-cards/{card_id}",
    response_model=ExclusiveCardResponse,
    status_code=status.HTTP_200_OK,
    summary="Update exclusive card (Admin)",
    description="Update an existing exclusive card (Admin only)"
)
async def update_exclusive_card(
    card_id: int,
    card_data: ExclusiveCardUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an exclusive card.

    Requires admin role.
    """
    service = ExclusiveCardService(db)
    card = await service.update_card(card_id, card_data)
    return ExclusiveCardResponse.model_validate(card)


@router.delete(
    "/admin/exclusive-cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete exclusive card (Admin)",
    description="Delete an exclusive card (Admin only)"
)
async def delete_exclusive_card(
    card_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an exclusive card.

    Requires admin role.
    """
    service = ExclusiveCardService(db)
    await service.delete_card(card_id)
    return None


# Featured Listings Endpoints
@router.put(
    "/admin/listings/{listing_id}/featured",
    response_model=ListingResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle listing featured status (Admin)",
    description="Toggle the featured status of a listing (Admin only)"
)
async def toggle_listing_featured(
    listing_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle the featured status of a listing.

    Requires admin role. Useful for marking listings as featured
    for the home screen.
    """
    service = ListingService(db)
    listing = await service.toggle_featured(listing_id)
    return ListingResponse.model_validate(listing)


# Popular Categories Endpoints
@router.put(
    "/admin/categories/{category_id}/popular",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle category popular status (Admin)",
    description="Toggle the popular status of a category (Admin only)"
)
async def toggle_category_popular(
    category_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle the popular status of a category.

    Requires admin role. Useful for marking categories as popular
    for the home screen popular games section.
    """
    # Get category
    category_service = CategoryService(db)
    category = await category_service.get_category(category_id)

    # Toggle popular status
    from app.repositories.category import CategoryRepository
    category_repo = CategoryRepository(db)
    updated = await category_repo.update(
        category_id,
        is_popular=not category.is_popular
    )
    await db.commit()

    # Return updated category
    updated_category = await category_service.get_category(category_id)
    return CategoryResponse.model_validate(updated_category)
