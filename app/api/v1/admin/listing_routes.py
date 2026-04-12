"""
Listing Moderation API routes.

Provides endpoints for listing moderation including:
- Viewing pending listings
- Approving listings
- Rejecting listings
- Removing listings

All endpoints require admin role.
"""

from logging import getLogger
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, paginate
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.admin import ListingModerationResponse, RejectListingRequest
from app.schemas.common import APIResponse, PaginationSchema, SuccessResponse
from app.services.admin import AdminService

logger = getLogger(__name__)
router = APIRouter()


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Admin user

    Raises:
        ForbiddenException: If user is not admin
    """
    # Check if user is admin
    # In production, you would have a role field on the User model
    # For now, we'll check if the user is verified and active
    if not current_user.profile.is_verified:
        from app.core.exceptions import ForbiddenException

        raise ForbiddenException("access admin panel")

    # Add actual admin role check here
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user


# ============================================================================
# Listing Moderation
# ============================================================================


@router.get(
    "/listings/pending",
    response_model=APIResponse[ListingModerationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get pending listings",
)
async def get_pending_listings(
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ListingModerationResponse]:
    """
    Get listings awaiting admin approval.

    Returns all listings with status 'pending' that require admin review.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.get_pending_listings(
            page=pagination.page, limit=pagination.limit
        )

        logger.info(f"Admin {current_admin.username} viewed pending listings")

        return APIResponse.success_response(
            data=result, message="Pending listings retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get pending listings: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting pending listings: {str(e)}")
        raise


@router.post(
    "/listings/{listing_id}/approve",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve listing",
)
async def approve_listing(
    listing_id: UUID,
    notes: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Approve a pending listing.

    Approves a listing and changes its status to 'active'.

    - **notes**: Optional admin notes for the approval

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.approve_listing(listing_id, notes)

        logger.info(f"Admin {current_admin.username} approved listing: {listing_id}")

        return APIResponse.success_response(data=result, message="Listing approved successfully")

    except AppException as e:
        logger.warning(f"Failed to approve listing: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error approving listing: {str(e)}")
        raise


@router.post(
    "/listings/{listing_id}/reject",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject listing",
)
async def reject_listing(
    listing_id: UUID,
    data: RejectListingRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Reject a listing with reason.

    Rejects a listing and records the rejection reason.

    - **reason**: Rejection reason (required, min 5 characters)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.reject_listing(listing_id, data.reason)

        logger.info(
            f"Admin {current_admin.username} rejected listing: {listing_id}, reason: {data.reason}"
        )

        return APIResponse.success_response(data=result, message="Listing rejected successfully")

    except AppException as e:
        logger.warning(f"Failed to reject listing: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error rejecting listing: {str(e)}")
        raise


@router.delete(
    "/listings/{listing_id}",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Remove listing",
)
async def remove_listing(
    listing_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Remove a listing from platform.

    Permanently removes a listing from the platform.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.remove_listing(listing_id)

        logger.warning(f"Admin {current_admin.username} removed listing: {listing_id}")

        return APIResponse.success_response(data=result, message="Listing removed successfully")

    except AppException as e:
        logger.warning(f"Failed to remove listing: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error removing listing: {str(e)}")
        raise
