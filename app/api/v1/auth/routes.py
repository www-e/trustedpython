"""
Authentication API routes.

Provides endpoints for user registration, login, password reset,
token refresh, logout, profile retrieval, and email verification.
"""

from logging import getLogger
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user as current_user_dep, get_db
from app.api.v1.auth.schemas import (
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    UserStats,
    VerifyEmailRequest,
)
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.common import APIResponse, SuccessResponse
from app.services.auth_service import AuthService
from app.utils.rate_limit import rate_limit_login, rate_limit_register

logger = getLogger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[RegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@rate_limit_register
async def register(
    data: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse[RegisterResponse]:
    """
    Register a new user account.

    - **username**: Unique username (3-50 characters, alphanumeric + underscore)
    - **email**: Valid email address
    - **phone**: Phone number (10+ digits)
    - **password**: Password (6+ characters)

    Returns created user with access and refresh tokens.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.register(data.model_dump())

        logger.info(f"New user registered: {result['user']['username']}")

        response_data = RegisterResponse(
            user=UserResponse(**result["user"]),
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result["expires_in"],
        )

        return APIResponse.success_response(data=response_data, message="Account created successfully")

    except AppException as e:
        logger.warning(f"Registration failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise


@router.post(
    "/login",
    response_model=APIResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
)
@rate_limit_login
async def login(
    data: LoginRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse[LoginResponse]:
    """
    Authenticate user and return tokens.

    - **username**: Username or email
    - **password**: User password

    Returns authenticated user with access and refresh tokens.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.login(data.model_dump())

        logger.info(f"User logged in: {result['user']['username']}")

        response_data = LoginResponse(
            user=UserResponse(**result["user"]),
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result["expires_in"],
        )

        return APIResponse.success_response(data=response_data, message="Login successful")

    except AppException as e:
        logger.warning(f"Login failed for {data.username}: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise


@router.post(
    "/forgot-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
)
async def forgot_password(
    data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Send password reset link to email.

    - **email**: Email address for password reset

    Returns success message if email is registered.
    """
    try:
        auth_service = AuthService(db)
        await auth_service.forgot_password(data.email)

        logger.info(f"Password reset requested for: {data.email}")

        return SuccessResponse.create(message="Password reset link sent to your email")

    except AppException as e:
        # For security, don't reveal if email exists
        logger.warning(f"Password reset requested for non-existent email: {data.email}")
        # Still return success to prevent email enumeration
        return SuccessResponse.create(message="Password reset link sent to your email")
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
)
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Reset password using token from email.

    - **token**: Password reset token from email
    - **new_password**: New password (6+ characters)

    Returns success message if password is reset.
    """
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(data.token, data.new_password)

        logger.info("Password reset successful")

        return SuccessResponse.create(message="Password reset successfully")

    except AppException as e:
        logger.warning(f"Password reset failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise


@router.post(
    "/refresh-token",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse[TokenResponse]:
    """
    Get new access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(data.refresh_token)

        logger.info("Token refreshed successfully")

        response_data = TokenResponse(**result)

        return APIResponse.success_response(data=response_data)

    except AppException as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        raise


@router.post(
    "/logout", response_model=SuccessResponse, status_code=status.HTTP_200_OK, summary="Logout user"
)
async def logout(
    current_user: User = Depends(current_user_dep), db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Invalidate user session.

    Requires authentication via Bearer token.

    Returns success message on logout.
    """
    try:
        # TODO: Get access token from request
        access_token = ""  # Will be implemented with token extraction

        auth_service = AuthService(db)
        await auth_service.logout(current_user.id, access_token)

        logger.info(f"User logged out: {current_user.username}")

        return SuccessResponse.create(message="Logged out successfully")

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise


@router.get(
    "/me",
    response_model=APIResponse[CurrentUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_user_profile(
    current_user: User = Depends(current_user_dep), db: AsyncSession = Depends(get_db)
) -> APIResponse[CurrentUserResponse]:
    """
    Get authenticated user profile with statistics.

    Requires authentication via Bearer token.

    Returns complete user profile with stats.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.get_current_user(current_user.id)

        stats = UserStats(**result["stats"])
        response_data = CurrentUserResponse(
            id=result["id"],
            username=result["username"],
            email=result["email"],
            phone=result["phone"],
            display_name=result["display_name"],
            avatar_url=result["avatar_url"],
            is_verified=result["is_verified"],
            created_at=result["created_at"],
            stats=stats,
        )

        return APIResponse.success_response(data=response_data)

    except AppException as e:
        logger.warning(f"Get current user failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise


@router.post(
    "/verify-email",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
)
async def verify_email(
    data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Verify user email address.

    - **token**: Email verification token from verification email

    Returns success message if email is verified.
    """
    try:
        auth_service = AuthService(db)
        await auth_service.verify_email(data.token)

        logger.info("Email verified successfully")

        return SuccessResponse.create(message="Email verified successfully")

    except AppException as e:
        logger.warning(f"Email verification failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Verify email error: {str(e)}")
        raise
