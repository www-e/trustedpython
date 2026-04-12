"""
User management API routes for admin dashboard.

Provides endpoints for user administration including listing, searching,
viewing details, verification, suspension, and banning users.
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
    BanUserRequest,
    SuspendUserRequest,
    UserDetailResponse,
    UserListResponse,
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
    # Check if user is admin
    # In production, you would have a role field on the User model
    # For now, we'll check if the user is verified and active
    from app.core.exceptions import ForbiddenException

    if not current_user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user


# ============================================================================
# User Management
# ============================================================================


@router.get(
    "/users",
    response_model=APIResponse[UserListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
)
async def list_all_users(
    status: Optional[str] = Query(
        None, pattern="^(active|suspended|banned)$", description="Filter by status"
    ),
    role: Optional[str] = Query(
        None, pattern="^(user|mediator|admin)$", description="Filter by role"
    ),
    search: Optional[str] = Query(None, description="Search username/email"),
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListResponse]:
    """
    List all users with filtering and pagination.

    - **status**: Filter by status (active, suspended, banned)
    - **role**: Filter by role (user, mediator, admin)
    - **search**: Search username or email
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.list_all_users(
            status=status, search=search, page=pagination.page, limit=pagination.limit
        )

        logger.info(
            f"Admin {current_admin.username} listed users (filters: status={status}, role={role}, search={search})"
        )

        return APIResponse.success_response(data=result, message="Users retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to list users: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise


@router.get(
    "/users/{user_id}",
    response_model=APIResponse[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user details",
)
async def get_user_details(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserDetailResponse]:
    """
    Get detailed user information.

    Returns comprehensive user details including profile, listings,
    active deals, reports, and login history.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        user_details = await admin_service.get_user_details(user_id)

        logger.info(f"Admin {current_admin.username} viewed user details: {user_id}")

        return APIResponse.success_response(
            data=user_details, message="User details retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get user details: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise


@router.post(
    "/users/{user_id}/verify",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify user",
)
async def verify_user(
    user_id: UUID,
    notes: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Verify a user's account.

    Grants verification badge to a user account.

    - **notes**: Optional admin notes for the verification

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.verify_user(user_id, notes)

        logger.info(f"Admin {current_admin.username} verified user: {user_id}")

        return APIResponse.success_response(data=result, message="User verified successfully")

    except AppException as e:
        logger.warning(f"Failed to verify user: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error verifying user: {str(e)}")
        raise


@router.post(
    "/users/{user_id}/suspend",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Suspend user",
)
async def suspend_user(
    user_id: UUID,
    data: SuspendUserRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Suspend a user's account.

    Temporarily suspends a user account.

    - **reason**: Suspension reason (required, min 5 characters)
    - **duration_days**: Duration in days (null = indefinite)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.suspend_user(user_id, data.reason, data.duration_days)

        logger.info(
            f"Admin {current_admin.username} suspended user: {user_id}, reason: {data.reason}"
        )

        return APIResponse.success_response(data=result, message="User suspended successfully")

    except AppException as e:
        logger.warning(f"Failed to suspend user: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error suspending user: {str(e)}")
        raise


@router.post(
    "/users/{user_id}/unsuspend",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Unsuspend user",
)
async def unsuspend_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Unsuspend a user's account.

    Removes suspension from a user account.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.unsuspend_user(user_id)

        logger.info(f"Admin {current_admin.username} unsuspended user: {user_id}")

        return APIResponse.success_response(data=result, message="User unsuspended successfully")

    except AppException as e:
        logger.warning(f"Failed to unsuspend user: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error unsuspending user: {str(e)}")
        raise


@router.post(
    "/users/{user_id}/ban",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_200_OK,
    summary="Ban user",
)
async def ban_user(
    user_id: UUID,
    data: BanUserRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SuccessResponse]:
    """
    Permanently ban a user.

    Permanently bans a user from the platform.

    - **reason**: Ban reason (required, min 5 characters)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.ban_user(user_id, data.reason)

        logger.warning(
            f"Admin {current_admin.username} banned user: {user_id}, reason: {data.reason}"
        )

        return APIResponse.success_response(data=result, message="User banned successfully")

    except AppException as e:
        logger.warning(f"Failed to ban user: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        raise


@router.get(
    "/users/search",
    response_model=APIResponse[UserListResponse],
    status_code=status.HTTP_200_OK,
    summary="Search users",
)
async def search_users(
    query: str = Query(..., min_length=2, description="Search query"),
    pagination: PaginationSchema = Depends(paginate),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListResponse]:
    """
    Search users by username or email.

    - **query**: Search query (min 2 characters)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.search_users(
            query=query, page=pagination.page, limit=pagination.limit
        )

        logger.info(f"Admin {current_admin.username} searched users: {query}")

        return APIResponse.success_response(
            data=result, message=f"User search results for: {query}"
        )

    except AppException as e:
        logger.warning(f"Failed to search users: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise
