"""Profile API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.common import APIResponse, PaginationSchema
from app.schemas.listing import (
    ProfileCreateListingRequest,
    ProfileUpdateListingRequest,
    UpdateListingStatusRequest,
    UploadImageResponse,
    UserListingDetailResponse,
    UserListingResponse,
    UserListingsListResponse,
)
from app.schemas.profile import (
    PublicProfileResponse,
    TradeHistoryListResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UploadAvatarResponse,
    UserProfileResponse,
    UserStatsResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/me", response_model=APIResponse[UserProfileResponse])
async def get_current_profile(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[UserProfileResponse]:
    """
    Get current user's full profile.

    Returns complete profile including stats, recent listings, and recent trades.
    """
    service = ProfileService(db)
    profile = await service.get_current_profile(current_user.id)
    return APIResponse.success_response(data=profile)


@router.get("/me/stats", response_model=APIResponse[UserStatsResponse])
async def get_user_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[UserStatsResponse]:
    """
    Get detailed user statistics.

    Returns comprehensive statistics including revenue, success rate, and response time.
    """
    service = ProfileService(db)
    stats = await service.get_user_stats(current_user.id)
    return APIResponse.success_response(data=stats)


@router.get("/me/trade-history", response_model=APIResponse[TradeHistoryListResponse])
async def get_trade_history(
    status: Optional[str] = Query(
        None, description="Filter by status: completed, pending, cancelled"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TradeHistoryListResponse]:
    """
    Get user's trade history.

    Returns paginated list of user's trades with optional status filter.
    """
    service = ProfileService(db)
    history = await service.get_trade_history(current_user.id, status, page, limit)
    pagination_data = history.pagination
    return APIResponse.success_response(
        data=history,
        pagination=PaginationSchema(
            page=pagination_data["page"],
            limit=pagination_data["limit"],
            total=pagination_data["total"],
            total_pages=pagination_data["total_pages"],
            has_next=pagination_data["has_next"],
            has_prev=pagination_data["has_prev"],
        ),
    )


@router.put("/update", response_model=APIResponse[UpdateProfileResponse])
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UpdateProfileResponse]:
    """
    Update user profile.

    Allows updating display name, phone, bio, and user role.
    """
    service = ProfileService(db)
    updated_profile = await service.update_profile(current_user.id, data)
    return APIResponse.success_response(
        data=updated_profile, message="Profile updated successfully"
    )


@router.post("/avatar", response_model=APIResponse[UploadAvatarResponse])
async def upload_avatar(
    avatar: UploadFile = File(..., description="Profile image (max 2MB, jpg/jpeg/png)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UploadAvatarResponse]:
    """
    Upload profile avatar.

    Uploads and sets user's profile avatar image.
    Max file size: 2MB. Allowed formats: JPG, JPEG, PNG.
    """
    # Validate file size
    file_data = await avatar.read()
    if len(file_data) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 2MB limit",
        )

    # Validate content type
    allowed_types = {"image/jpeg", "image/jpg", "image/png"}
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid file type. Only JPG, JPEG, PNG allowed",
        )

    service = ProfileService(db)
    avatar_filename = avatar.filename or "avatar.jpg"
    result = await service.upload_avatar(current_user.id, file_data, avatar_filename)
    return APIResponse.success_response(data=result, message="Avatar uploaded successfully")


@router.get("/{userId}", response_model=APIResponse[PublicProfileResponse])
async def get_public_profile(
    userId: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[PublicProfileResponse]:
    """
    Get another user's public profile.

    Returns public profile information without sensitive data (email, phone).
    """
    service = ProfileService(db)
    profile = await service.get_public_profile(userId)
    return APIResponse.success_response(data=profile)


@router.get("/listings", response_model=APIResponse[UserListingsListResponse])
async def get_user_listings(
    status: Optional[str] = Query(None, description="Filter by status: active, sold, expired"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListingsListResponse]:
    """
    Get user's listings.

    Returns paginated list of user's listings with optional status filter.
    """
    service = ProfileService(db)
    listings = await service.get_user_listings(current_user.id, status, page, limit)
    pagination_data = listings.pagination
    return APIResponse.success_response(
        data=listings,
        pagination=PaginationSchema(
            page=pagination_data["page"],
            limit=pagination_data["limit"],
            total=pagination_data["total"],
            total_pages=pagination_data["total_pages"],
            has_next=pagination_data["has_next"],
            has_prev=pagination_data["has_prev"],
        ),
    )


@router.post("/listings", response_model=APIResponse[UserListingResponse], status_code=201)
async def create_listing(
    data: ProfileCreateListingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListingResponse]:
    """
    Create a new listing.

    Creates a new listing for the current user.
    Rate limit: Maximum 10 listings per day.
    """
    service = ProfileService(db)
    listing = await service.create_listing(current_user.id, data)
    return APIResponse.success_response(data=listing, message="Listing created successfully")


@router.get("/listings/{id}", response_model=APIResponse[UserListingDetailResponse])
async def get_listing_details(
    id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[UserListingDetailResponse]:
    """
    Get listing details.

    Returns detailed information about a specific listing.
    """
    service = ProfileService(db)
    listing = await service.get_listing_details(id)
    return APIResponse.success_response(data=listing)


@router.put("/listings/{id}", response_model=APIResponse[UserListingResponse])
async def update_listing(
    id: UUID,
    data: ProfileUpdateListingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListingResponse]:
    """
    Update a listing.

    Updates an existing listing. User can only update their own listings.
    """
    service = ProfileService(db)
    listing = await service.update_listing(id, current_user.id, data)
    return APIResponse.success_response(data=listing, message="Listing updated successfully")


@router.delete("/listings/{id}", response_model=APIResponse[dict])
async def delete_listing(
    id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Delete a listing.

    Deletes a listing. User can only delete their own listings.
    """
    service = ProfileService(db)
    result = await service.delete_listing(id, current_user.id)
    return APIResponse.success_response(data=result, message="Listing deleted successfully")


@router.put("/listings/{id}/status", response_model=APIResponse[UserListingResponse])
async def update_listing_status(
    id: UUID,
    data: UpdateListingStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListingResponse]:
    """
    Update listing status.

    Updates the status of a listing (active, sold, expired).
    User can only update their own listings.
    """
    service = ProfileService(db)
    listing = await service.update_listing_status(id, current_user.id, data.status)
    return APIResponse.success_response(data=listing, message="Listing status updated successfully")


@router.post(
    "/listings/upload-image", response_model=APIResponse[UploadImageResponse], status_code=201
)
async def upload_listing_image(
    image: UploadFile = File(..., description="Listing image (max 5MB, jpg/jpeg/png)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UploadImageResponse]:
    """
    Upload a listing image.

    Uploads an image that can be attached to a listing.
    Max file size: 5MB. Allowed formats: JPG, JPEG, PNG.
    Maximum 10 images per listing.
    """
    # Validate file size
    file_data = await image.read()
    if len(file_data) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit",
        )

    # Validate content type
    allowed_types = {"image/jpeg", "image/jpg", "image/png"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid file type. Only JPG, JPEG, PNG allowed",
        )

    service = ProfileService(db)
    image_filename = image.filename or "image.jpg"
    result = await service.upload_listing_image(file_data, image_filename)
    return APIResponse.success_response(data=result, message="Image uploaded successfully")
