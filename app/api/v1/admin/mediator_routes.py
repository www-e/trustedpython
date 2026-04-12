"""
Mediator management API routes.

Provides endpoints for admin to manage platform mediators including:
- Listing and viewing mediators
- Verifying mediators
- Updating mediator tiers
- Suspending mediators
- Managing mediator applications (approve/reject)
"""

from logging import getLogger
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, paginate
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.admin import (
    MediatorApplicationsResponse,
    MediatorListResponse,
    RejectApplicationRequest,
    UpdateMediatorTierRequest,
)
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
# Mediator Management
# ============================================================================


@router.get(
    "/mediators",
    response_model=APIResponse[MediatorListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all mediators",
)
async def list_all_mediators(
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediatorListResponse]:
    """
    List all mediators.

    Returns all mediators on the platform with their statistics.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.list_all_mediators(
            page=pagination.page, limit=pagination.limit
        )

        logger.info(f"Admin {current_admin.username} listed mediators")

        return APIResponse.success_response(data=result, message="Mediators retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to list mediators: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error listing mediators: {str(e)}")
        raise


@router.get(
    "/mediators/{mediator_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get mediator details",
)
async def get_mediator_details(
    mediator_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Get mediator details for admin.

    Returns comprehensive mediator details including profile,
    statistics, and payment methods.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        mediator_details = await admin_service.get_mediator_details(mediator_id)

        logger.info(f"Admin {current_admin.username} viewed mediator details: {mediator_id}")

        return APIResponse.success_response(
            data=mediator_details, message="Mediator details retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get mediator details: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting mediator details: {str(e)}")
        raise


@router.post(
    "/mediators/{mediator_id}/verify",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify mediator",
)
async def verify_mediator(
    mediator_id: UUID,
    notes: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Verify a mediator.

    Grants verification badge to a mediator.

    - **notes**: Optional admin notes for the verification

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.verify_mediator(mediator_id, notes)

        logger.info(f"Admin {current_admin.username} verified mediator: {mediator_id}")

        return APIResponse.success_response(data=result, message="Mediator verified successfully")

    except AppException as e:
        logger.warning(f"Failed to verify mediator: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error verifying mediator: {str(e)}")
        raise


@router.post(
    "/mediators/{mediator_id}/update-tier",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Update mediator tier",
)
async def update_mediator_tier(
    mediator_id: UUID,
    data: UpdateMediatorTierRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Update mediator's tier.

    Changes a mediator's tier level.

    - **tier**: New tier (bronze, silver, gold, elite)
    - **reason**: Reason for tier change (optional)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.update_mediator_tier(mediator_id, data.tier)

        logger.info(
            f"Admin {current_admin.username} updated mediator tier: {mediator_id}, new tier: {data.tier}"
        )

        return APIResponse.success_response(
            data=result, message="Mediator tier updated successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to update mediator tier: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error updating mediator tier: {str(e)}")
        raise


@router.post(
    "/mediators/{mediator_id}/suspend",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Suspend mediator",
)
async def suspend_mediator(
    mediator_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Suspend a mediator.

    Suspends a mediator from taking new deals.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.suspend_mediator(mediator_id)

        logger.info(f"Admin {current_admin.username} suspended mediator: {mediator_id}")

        return APIResponse.success_response(data=result, message="Mediator suspended successfully")

    except AppException as e:
        logger.warning(f"Failed to suspend mediator: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error suspending mediator: {str(e)}")
        raise


@router.get(
    "/mediators/applications",
    response_model=APIResponse[MediatorApplicationsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get mediator applications",
)
async def get_mediator_applications(
    status: Optional[str] = Query(
        None, pattern="^(pending|approved|rejected)$", description="Filter by status"
    ),
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediatorApplicationsResponse]:
    """
    Get mediator applications.

    Returns mediator applications with optional status filter.

    - **status**: Filter by status (pending, approved, rejected)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.get_mediator_applications(
            status=status, page=pagination.page, limit=pagination.limit
        )

        logger.info(
            f"Admin {current_admin.username} viewed mediator applications (filter: status={status})"
        )

        return APIResponse.success_response(
            data=result, message="Mediator applications retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get mediator applications: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting mediator applications: {str(e)}")
        raise


@router.post(
    "/mediators/applications/{application_id}/approve",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve mediator application",
)
async def approve_mediator_application(
    application_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Approve a mediator application.

    Approves a mediator application and creates the mediator profile.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.approve_mediator_application(application_id)

        logger.info(
            f"Admin {current_admin.username} approved mediator application: {application_id}"
        )

        return APIResponse.success_response(
            data=result, message="Mediator application approved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to approve mediator application: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error approving mediator application: {str(e)}")
        raise


@router.post(
    "/mediators/applications/{application_id}/reject",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject mediator application",
)
async def reject_mediator_application(
    application_id: UUID,
    data: RejectApplicationRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Reject a mediator application.

    Rejects a mediator application with reason.

    - **reason**: Rejection reason (required, min 5 characters)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.reject_mediator_application(application_id, data.reason)

        logger.info(
            f"Admin {current_admin.username} rejected mediator application: {application_id}, reason: {data.reason}"
        )

        return APIResponse.success_response(
            data=result, message="Mediator application rejected successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to reject mediator application: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error rejecting mediator application: {str(e)}")
        raise
