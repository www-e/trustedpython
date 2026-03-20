"""Listing endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.deps import get_db, get_current_active_user
from app.services.listing_service import ListingService
from app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    ListingListResponse,
    ListingImageCreate,
    ListingImageResponse
)
from app.models.user import User
from app.models.enums import GameType

router = APIRouter()


@router.post(
    "/listings",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
    description="Create a new gaming account listing (seller only)"
)
async def create_listing(
    listing_data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new listing.

    Requires seller role. Listings start in DRAFT status.
    """
    # Check seller role
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can create listings")

    service = ListingService(db)
    listing = await service.create_listing(current_user.id, listing_data)
    return ListingResponse.model_validate(listing)


@router.get(
    "/listings",
    response_model=List[ListingResponse],
    summary="Get all listings",
    description="Get list of all active listings with optional filters"
)
async def get_listings(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    active_only: bool = Query(True, description="Only show active listings"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all listings.

    Query parameters:
    - category_id: Filter by category ID
    - active_only: Only return active listings (default: true)
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (pagination)
    """
    service = ListingService(db)
    listings = await service.get_all_listings(active_only, category_id, skip, limit)
    return [ListingResponse.model_validate(l) for l in listings]


@router.get(
    "/listings/featured",
    response_model=List[ListingResponse],
    summary="Get featured listings",
    description="Get featured active listings"
)
async def get_featured_listings(
    limit: int = Query(10, ge=1, le=50, description="Maximum listings to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get featured listings.

    Returns listings marked as featured, ordered by newest first.
    """
    service = ListingService(db)
    listings = await service.get_featured_listings(limit)
    return [ListingResponse.model_validate(l) for l in listings]


@router.get(
    "/listings/search",
    response_model=List[ListingResponse],
    summary="Search listings",
    description="Search listings with filters"
)
async def search_listings(
    q: Optional[str] = Query(None, description="Search query for title/description"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    game_type: Optional[GameType] = Query(None, description="Filter by game type"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search listings with multiple filters.

    Query parameters:
    - q: Search query for title and description
    - category_id: Filter by category
    - game_type: Filter by game type
    - min_price: Minimum price
    - max_price: Maximum price
    - skip: Pagination offset
    - limit: Maximum results
    """
    service = ListingService(db)
    listings = await service.search_listings(
        query=q,
        category_id=category_id,
        game_type=game_type,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit
    )
    return [ListingResponse.model_validate(l) for l in listings]


@router.get(
    "/listings/my",
    response_model=List[ListingResponse],
    summary="Get my listings",
    description="Get current user's listings (seller only)"
)
async def get_my_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's listings.

    Returns all listings created by the authenticated seller.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers have listings")

    service = ListingService(db)
    listings = await service.get_seller_listings(current_user.id, skip, limit)
    return [ListingResponse.model_validate(l) for l in listings]


@router.get(
    "/listings/{listing_id}",
    response_model=ListingResponse,
    summary="Get listing by ID",
    description="Get a specific listing with full details"
)
async def get_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a listing by ID.

    Returns listing details including all images.
    Increments view count.
    """
    service = ListingService(db)
    listing = await service.get_listing(listing_id)
    return ListingResponse.model_validate(listing)


@router.patch(
    "/listings/{listing_id}",
    response_model=ListingResponse,
    summary="Update a listing",
    description="Update listing details (seller only)"
)
async def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a listing.

    Only the seller who created the listing can update it.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can update listings")

    service = ListingService(db)
    listing = await service.update_listing(listing_id, current_user.id, listing_data)
    return ListingResponse.model_validate(listing)


@router.delete(
    "/listings/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a listing",
    description="Delete a listing (seller only)"
)
async def delete_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a listing.

    Only the seller who created the listing can delete it.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can delete listings")

    service = ListingService(db)
    await service.delete_listing(listing_id, current_user.id)
    return None


@router.post(
    "/listings/{listing_id}/publish",
    response_model=ListingResponse,
    summary="Publish a listing",
    description="Publish a draft listing (seller only)"
)
async def publish_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Publish a listing.

    Changes listing status from DRAFT to ACTIVE.
    Only the seller who created the listing can publish it.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can publish listings")

    service = ListingService(db)
    listing = await service.publish_listing(listing_id, current_user.id)
    return ListingResponse.model_validate(listing)


@router.post(
    "/listings/{listing_id}/pause",
    response_model=ListingResponse,
    summary="Pause a listing",
    description="Pause an active listing (seller only)"
)
async def pause_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pause a listing.

    Changes listing status from ACTIVE to PAUSED.
    Only the seller who created the listing can pause it.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can pause listings")

    service = ListingService(db)
    listing = await service.pause_listing(listing_id, current_user.id)
    return ListingResponse.model_validate(listing)


@router.post(
    "/listings/{listing_id}/images",
    response_model=ListingImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add image to listing",
    description="Add an image to a listing (seller only)"
)
async def add_listing_image(
    listing_id: int,
    image_data: ListingImageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add an image to a listing.

    Only the seller who created the listing can add images.
    """
    from app.models.enums import UserRole
    if current_user.role != UserRole.SELLER:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only sellers can add listing images")

    service = ListingService(db)
    image = await service.add_listing_image(listing_id, current_user.id, image_data)
    return ListingImageResponse.model_validate(image)


# Include router in API v1
api_router.include_router(router, tags=["Listings"])
