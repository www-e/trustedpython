"""
Reports and Moderation API routes.

Provides endpoints for managing user reports, viewing report details,
resolving reports, and managing blocked/banned users.
"""

from logging import getLogger
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, paginate
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.admin import BlockedUsersResponse, ReportsResponse, ResolveReportRequest
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
# Reports & Moderation
# ============================================================================


@router.get(
    "/reports",
    response_model=APIResponse[ReportsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user reports",
)
async def get_reports(
    status: Optional[str] = Query(
        None, pattern="^(pending|resolved|dismissed)$", description="Filter by status"
    ),
    type: Optional[str] = Query(
        None, pattern="^(user|listing|message|deal)$", description="Filter by type"
    ),
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReportsResponse]:
    """
    Get user reports for moderation.

    Returns user reports with optional filters.

    - **status**: Filter by status (pending, resolved, dismissed)
    - **type**: Filter by type (user, listing, message, deal)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.get_reports(
            status=status, type=type, page=pagination.page, limit=pagination.limit
        )

        logger.info(
            f"Admin {current_admin.username} viewed reports (filters: status={status}, type={type})"
        )

        return APIResponse.success_response(data=result, message="Reports retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to get reports: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting reports: {str(e)}")
        raise


@router.get(
    "/reports/{report_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get report details",
)
async def get_report_details(
    report_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Get report details.

    Returns comprehensive report details including target information
    and resolution status.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        report_details = await admin_service.get_report_details(report_id)

        logger.info(f"Admin {current_admin.username} viewed report details: {report_id}")

        return APIResponse.success_response(
            data=report_details, message="Report details retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get report details: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting report details: {str(e)}")
        raise


@router.post(
    "/reports/{report_id}/resolve",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Resolve report",
)
async def resolve_report(
    report_id: UUID,
    data: ResolveReportRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Resolve a report.

    Marks a report as resolved with the action taken.

    - **action**: Action taken (none, warning, suspend, ban, remove_content)
    - **notes**: Resolution notes (required, min 5 characters)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.resolve_report(report_id, data.action, data.notes)

        logger.info(
            f"Admin {current_admin.username} resolved report: {report_id}, action: {data.action}"
        )

        return APIResponse.success_response(data=result, message="Report resolved successfully")

    except AppException as e:
        logger.warning(f"Failed to resolve report: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error resolving report: {str(e)}")
        raise


@router.get(
    "/blocked-users",
    response_model=APIResponse[BlockedUsersResponse],
    status_code=status.HTTP_200_OK,
    summary="Get blocked users",
)
async def get_blocked_users(
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BlockedUsersResponse]:
    """
    Get blocked/banned users.

    Returns all suspended and banned users.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.get_blocked_users(page=pagination.page, limit=pagination.limit)

        logger.info(f"Admin {current_admin.username} viewed blocked users")

        return APIResponse.success_response(
            data=result, message="Blocked users retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get blocked users: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting blocked users: {str(e)}")
        raise


@router.post(
    "/blocked-users/{user_id}/unblock",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Unblock user",
)
async def unblock_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Unblock a user.

    Removes suspension/ban from a user.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.unblock_user(user_id)

        logger.info(f"Admin {current_admin.username} unblocked user: {user_id}")

        return APIResponse.success_response(data=result, message="User unblocked successfully")

    except AppException as e:
        logger.warning(f"Failed to unblock user: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error unblocking user: {str(e)}")
        raise
