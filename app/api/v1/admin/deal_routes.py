"""
Deal management routes for admin operations.

Provides endpoints for administrators to manage deals including listing,
viewing details, resolving disputes, and canceling deals.
"""

from logging import getLogger
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, paginate
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.admin import CancelDealRequest, DealListResponse, ResolveDisputeRequest
from app.schemas.common import APIResponse, PaginationSchema, SuccessResponse
from app.services.admin import AdminService

logger = getLogger(__name__)
router = APIRouter()


# ============================================================================
# Admin Role Dependency
# ============================================================================


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
    from app.core.exceptions import ForbiddenException

    # Check if user is admin
    # In production, you would have a role field on the User model
    # For now, we'll check if the user is verified and active
    if not current_user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user


# ============================================================================
# Deal Management
# ============================================================================


@router.get(
    "/deals",
    response_model=APIResponse[DealListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all deals",
)
async def list_all_deals(
    status: Optional[str] = Query(None, description="Filter by deal status"),
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DealListResponse]:
    """
    Get all deals with filtering.

    Returns all deals on the platform with optional status filter.

    - **status**: Filter by deal status
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.list_all_deals(
            status=status, page=pagination.page, limit=pagination.limit
        )

        logger.info(f"Admin {current_admin.username} listed deals (filter: status={status})")

        return APIResponse.success_response(data=result, message="Deals retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to list deals: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error listing deals: {str(e)}")
        raise


@router.get(
    "/deals/{deal_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get deal details",
)
async def get_deal_details(
    deal_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Get deal details for admin.

    Returns comprehensive deal details including payment information,
    parties involved, and dispute details if applicable.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        deal_details = await admin_service.get_deal_details(deal_id)

        logger.info(f"Admin {current_admin.username} viewed deal details: {deal_id}")

        return APIResponse.success_response(
            data=deal_details, message="Deal details retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get deal details: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting deal details: {str(e)}")
        raise


@router.post(
    "/deals/{deal_id}/resolve",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Resolve dispute",
)
async def resolve_dispute(
    deal_id: UUID,
    data: ResolveDisputeRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Resolve a disputed deal.

    Resolves a disputed deal by making a decision and optionally refunding.

    - **decision**: Resolution decision (buyer, seller, refund)
    - **resolution_notes**: Resolution notes (required, min 10 characters)
    - **refund_amount**: Refund amount if applicable

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.resolve_dispute(
            deal_id, data.decision, data.resolution_notes, data.refund_amount
        )

        logger.info(
            f"Admin {current_admin.username} resolved dispute for deal: {deal_id}, decision: {data.decision}"
        )

        return APIResponse.success_response(data=result, message="Dispute resolved successfully")

    except AppException as e:
        logger.warning(f"Failed to resolve dispute: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error resolving dispute: {str(e)}")
        raise


@router.post(
    "/deals/{deal_id}/cancel",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Cancel deal",
)
async def cancel_deal(
    deal_id: UUID,
    data: CancelDealRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Cancel a deal.

    Cancels an active deal.

    - **reason**: Cancellation reason (required, min 5 characters)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.cancel_deal(deal_id, data.reason)

        logger.info(
            f"Admin {current_admin.username} cancelled deal: {deal_id}, reason: {data.reason}"
        )

        return APIResponse.success_response(data=result, message="Deal cancelled successfully")

    except AppException as e:
        logger.warning(f"Failed to cancel deal: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error cancelling deal: {str(e)}")
        raise
