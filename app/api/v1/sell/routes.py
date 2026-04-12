"""
Sell Flow API routes.

Handles listing creation, preview, image upload, category/game management,
publishing, and seller analytics.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import (
    AppException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.schemas.common import APIResponse
from app.schemas.listing import (
    CategoryResponse,
    CreateListingRequest,
    GameResponse,
    ImageResponse,
    ListingResponse,
    PreviewListingRequest,
    PreviewListingResponse,
    PublishResponse,
    SellAnalyticsResponse,
    UpdateListingRequest,
)
from app.services.sell_service import SellService

router = APIRouter(tags=["Selling"])
security = HTTPBearer()


@router.post(
    "/listings",
    response_model=APIResponse[ListingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new listing",
    description="Create a new listing (initially as draft)",
)
async def create_listing(
    data: CreateListingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[ListingResponse]:
    """
    Create a new listing.

    - **title**: Listing title (3-100 characters)
    - **price**: Listing price (must be > 0)
    - **game**: Game name
    - **category_id**: Category UUID
    - **description**: Optional description (max 2000 chars)
    - **image_ids**: List of uploaded image IDs
    - **is_premium**: Premium listing status
    - **tier**: Premium tier (Regular, Gold, Elite)
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        listing = await service.create_listing(user_id, data)

        return APIResponse.success_response(data=listing, message="Listing created successfully")
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.post(
    "/listings/preview",
    response_model=APIResponse[PreviewListingResponse],
    status_code=status.HTTP_200_OK,
    summary="Preview listing",
    description="Preview how listing will appear before publishing",
)
async def preview_listing(
    data: PreviewListingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[PreviewListingResponse]:
    """
    Preview a listing.

    - **title**: Listing title
    - **price**: Listing price
    - **game**: Game name
    - **description**: Optional description
    - **image_urls**: List of image URLs
    - **is_premium**: Premium listing status
    - **tier**: Premium tier
    """
    try:
        service = SellService(db)

        preview = await service.preview_listing(data)

        return APIResponse.success_response(data=preview, message="Preview generated successfully")
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.get(
    "/categories",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get categories",
    description="Get all available listing categories",
)
async def get_categories(db: AsyncSession = Depends(get_db)) -> APIResponse[dict]:
    """
    Get all available categories.

    Returns a list of categories with listing counts.
    """
    try:
        service = SellService(db)
        categories = await service.get_categories()

        return APIResponse.success_response(
            data={"categories": categories}, message="Categories retrieved successfully"
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.get(
    "/games",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get games",
    description="Get all supported games for listings",
)
async def get_games(db: AsyncSession = Depends(get_db)) -> APIResponse[dict]:
    """
    Get all supported games.

    Returns a list of games with active listing counts and average prices.
    """
    try:
        service = SellService(db)
        games = await service.get_games()

        return APIResponse.success_response(
            data={"games": games}, message="Games retrieved successfully"
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.post(
    "/upload-image",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Upload listing images",
    description="Upload images for a listing (max 10)",
)
async def upload_images(
    images: List[UploadFile] = File(..., min_length=1, max_length=10),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[dict]:
    """
    Upload listing images.

    - **images**: List of image files (max 10, 5MB each)
    - Supported formats: jpg, jpeg, png, webp
    - Recommended size: 1200x800px minimum
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        # Validate file types
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        max_size = 5 * 1024 * 1024  # 5MB

        files_data = []
        filenames: list[str] = []

        for image in images:
            # Check content type
            if image.content_type not in allowed_types:
                raise ValidationException(
                    f"Invalid file type: {image.content_type}. " f"Allowed: jpg, jpeg, png, webp"
                )

            # Read file content
            content = await image.read()

            # Check file size
            if len(content) > max_size:
                raise ValidationException(f"File {image.filename} exceeds 5MB limit")

            # Use a default filename if image.filename is None
            filename = image.filename or f"upload_{len(filenames)}"
            files_data.append((filename, content, image.content_type))
            filenames.append(filename)

        # Upload images
        uploaded_images = await service.upload_images(user_id, files_data, filenames)

        return APIResponse.success_response(
            data={"images": uploaded_images},
            message=f"Successfully uploaded {len(uploaded_images)} image(s)",
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.put(
    "/listings/{listing_id}",
    response_model=APIResponse[ListingResponse],
    status_code=status.HTTP_200_OK,
    summary="Update listing",
    description="Update an existing draft listing",
)
async def update_listing(
    listing_id: UUID,
    data: UpdateListingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[ListingResponse]:
    """
    Update an existing listing.

    All fields are optional. Only provided fields will be updated.
    Only the listing owner can update.
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        listing = await service.update_listing(listing_id, user_id, data)

        return APIResponse.success_response(data=listing, message="Listing updated successfully")
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.post(
    "/listings/{listing_id}/publish",
    response_model=APIResponse[PublishResponse],
    status_code=status.HTTP_200_OK,
    summary="Publish listing",
    description="Publish a draft listing to make it visible",
)
async def publish_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[PublishResponse]:
    """
    Publish a draft listing.

    Only the listing owner can publish.
    Listing must be in 'draft' or 'expired' status.
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        result = await service.publish_listing(listing_id, user_id)

        return APIResponse.success_response(data=result, message="Listing published successfully")
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.post(
    "/listings/{listing_id}/unpublish",
    response_model=APIResponse[PublishResponse],
    status_code=status.HTTP_200_OK,
    summary="Unpublish listing",
    description="Unpublish a listing (hide from marketplace)",
)
async def unpublish_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[PublishResponse]:
    """
    Unpublish a listing.

    Only the listing owner can unpublish.
    Listing must be in 'active' status.
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        result = await service.unpublish_listing(listing_id, user_id)

        return APIResponse.success_response(data=result, message="Listing unpublished successfully")
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )


@router.get(
    "/analytics",
    response_model=APIResponse[SellAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get sell analytics",
    description="Get analytics for user's listings",
)
async def get_analytics(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> APIResponse[SellAnalyticsResponse]:
    """
    Get sell analytics for the current user.

    Returns:
    - Total listings count
    - Active listings count
    - Sold listings count
    - Total views
    - Total revenue
    - Average time to sell
    - Top performing listing
    - Recent activity
    """
    try:
        service = SellService(db)
        user_id = UUID(current_user["sub"])

        analytics = await service.get_analytics(user_id)

        return APIResponse.success_response(
            data=analytics, message="Analytics retrieved successfully"
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code, detail={"error_code": e.error_code, "message": e.message}
        )
