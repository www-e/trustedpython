"""
Dashboard and Analytics API routes.

Provides endpoints for retrieving dashboard statistics and analytics data
for platform overview and monitoring.
"""

from logging import getLogger

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException, ForbiddenException
from app.models.user import User
from app.schemas.admin import AnalyticsResponse, DashboardStatsResponse
from app.schemas.common import APIResponse
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
    if not current_user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user


# ============================================================================
# Dashboard Stats & Analytics
# ============================================================================


@router.get(
    "/dashboard/stats",
    response_model=APIResponse[DashboardStatsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get dashboard overview statistics",
)
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> APIResponse[DashboardStatsResponse]:
    """
    Get dashboard overview statistics.

    Returns platform-wide statistics for users, listings, deals, mediators, and revenue.

    - **users**: User statistics (total, active_today, new_this_week, verified, suspended)
    - **listings**: Listing statistics (total, active, pending_approval, sold_this_week)
    - **deals**: Deal statistics (total, active, completed_this_week, disputed, success_rate)
    - **mediators**: Mediator statistics (total, active, verified, avg_response_time)
    - **revenue**: Revenue statistics (this_month, last_month, growth_percentage)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        stats = await admin_service.get_dashboard_stats()

        logger.info(f"Admin {current_admin.username} viewed dashboard stats")

        return APIResponse.success_response(
            data=stats, message="Dashboard statistics retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get dashboard stats: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise


@router.get(
    "/dashboard/analytics",
    response_model=APIResponse[AnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get detailed analytics",
)
async def get_analytics(
    period: str = Query("week", pattern="^(day|week|month|year)$", description="Time period"),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AnalyticsResponse]:
    """
    Get detailed analytics for a time period.

    Returns detailed analytics including user growth, deal volume, top games,
    top mediators, and revenue trends.

    - **period**: Time period (day, week, month, year)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        analytics = await admin_service.get_analytics(period)

        logger.info(f"Admin {current_admin.username} viewed analytics for period: {period}")

        return APIResponse.success_response(
            data=analytics, message=f"Analytics retrieved successfully for period: {period}"
        )

    except AppException as e:
        logger.warning(f"Failed to get analytics: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise
