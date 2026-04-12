"""
Admin-specific dependencies for route handlers.

Provides dependency injection functions for admin authentication and authorization.
"""

from fastapi import Depends

from app.api.deps import get_current_user
from app.core.exceptions import ForbiddenException
from app.models.user import User


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user.

    Verifies that the current authenticated user has admin privileges.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        User: The admin user

    Raises:
        ForbiddenException: If user is not verified/authorized for admin access

    Note:
        In production, implement proper role-based access control.
        This is a placeholder that checks verification status.
    """
    # Check if user is verified (temporary admin check)
    # In production, you would check a role field on the User model
    if not current_user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here when User model has role field
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user
