"""Security routes for user security operations"""

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.models.user import User
from app.schemas.security import (
    AuditLogResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    FreezeAccountRequest,
    LoginHistoryResponse,
    ReportSuspiciousActivityRequest,
    SecurityScoreResponse,
    SecuritySettingsResponse,
    SuccessResponse,
    TwoFactorDisableRequest,
    TwoFactorEnableRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UpdateSecuritySettingsRequest,
)
from app.services.security_service import SecurityService
from app.utils.rate_limit import rate_limit

router = APIRouter()


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change user password with current password verification",
)
@rate_limit(requests=3, window=60)  # 3 attempts per minute
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Change user password"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Verify user is not frozen
    if current_user.is_frozen:
        raise ValidationError("Account is frozen. Please contact support.")

    return await service.change_password(current_user.id, data)


@router.post(
    "/logout-all",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout all sessions",
    description="Logout user from all devices by invalidating all refresh tokens",
)
@rate_limit(requests=5, window=60)  # 5 attempts per minute
async def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Logout from all sessions"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.logout_all_sessions(current_user.id)


@router.get(
    "/login-history",
    response_model=LoginHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get login history",
    description="Retrieve user's login history with pagination",
)
@rate_limit(requests=30, window=60)  # 30 requests per minute
async def get_login_history(
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get login history"""
    service = SecurityService(db)

    # Validate pagination
    if page < 1:
        raise ValidationError("Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise ValidationError("Page size must be between 1 and 100")

    return await service.get_login_history(
        current_user.id, page=page, page_size=page_size, status_filter=status_filter
    )


@router.get(
    "/settings",
    response_model=SecuritySettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get security settings",
    description="Retrieve user's security settings",
)
@rate_limit(requests=30, window=60)  # 30 requests per minute
async def get_security_settings(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """Get security settings"""
    service = SecurityService(db)
    return await service.get_security_settings(current_user.id)


@router.put(
    "/settings",
    response_model=SecuritySettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update security settings",
    description="Update user's security settings",
)
@rate_limit(requests=10, window=60)  # 10 requests per minute
async def update_security_settings(
    request: Request,
    data: UpdateSecuritySettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update security settings"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.update_security_settings(current_user.id, data)


@router.post(
    "/enable-2fa",
    response_model=TwoFactorSetupResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable two-factor authentication",
    description="Enable 2FA for the user account. Returns QR code and backup codes.",
)
@rate_limit(requests=5, window=60)  # 5 attempts per minute
async def enable_2fa(
    request: Request,
    data: TwoFactorEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Enable two-factor authentication"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Verify user is not frozen
    if current_user.is_frozen:
        raise ValidationError("Account is frozen. Please contact support.")

    return await service.enable_2fa(current_user.id, data.password)


@router.post(
    "/verify-2fa",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify 2FA setup",
    description="Verify TOTP code to complete 2FA setup",
)
@rate_limit(requests=10, window=60)  # 10 attempts per minute
async def verify_2fa(
    request: Request,
    data: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify 2FA code"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.verify_2fa(current_user.id, data.code)


@router.post(
    "/disable-2fa",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable two-factor authentication",
    description="Disable 2FA for the user account",
)
@rate_limit(requests=5, window=60)  # 5 attempts per minute
async def disable_2fa(
    request: Request,
    data: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Disable two-factor authentication"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Verify user is not frozen
    if current_user.is_frozen:
        raise ValidationError("Account is frozen. Please contact support.")

    return await service.disable_2fa(current_user.id, data.code)


@router.get(
    "/audit-log",
    response_model=AuditLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get audit log",
    description="Retrieve user's security audit log with pagination",
)
@rate_limit(requests=30, window=60)  # 30 requests per minute
async def get_audit_log(
    page: int = 1,
    page_size: int = 20,
    event_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get audit log"""
    service = SecurityService(db)

    # Validate pagination
    if page < 1:
        raise ValidationError("Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise ValidationError("Page size must be between 1 and 100")

    return await service.get_audit_log(
        current_user.id, page=page, page_size=page_size, event_type=event_type
    )


@router.post(
    "/report-suspicious",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Report suspicious activity",
    description="Report suspicious activity on the account",
)
@rate_limit(requests=10, window=60)  # 10 requests per minute
async def report_suspicious_activity(
    request: Request,
    data: ReportSuspiciousActivityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Report suspicious activity"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.report_suspicious_activity(
        current_user.id, data.activity_type, data.description, data.evidence
    )


@router.post(
    "/freeze-account",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Freeze account",
    description="Freeze user account for security reasons",
)
@rate_limit(requests=3, window=60)  # 3 attempts per minute
async def freeze_account(
    request: Request,
    data: FreezeAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Freeze account"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.freeze_account(current_user.id, data.reason, data.duration_hours)


@router.post(
    "/unfreeze-account",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Unfreeze account",
    description="Unfreeze user account",
)
@rate_limit(requests=5, window=60)  # 5 attempts per minute
async def unfreeze_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Unfreeze account"""
    service = SecurityService(db)

    # Get IP address and user agent for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.unfreeze_account(current_user.id)


@router.get(
    "/score",
    response_model=SecurityScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get security score",
    description="Calculate and retrieve user's security score with recommendations",
)
@rate_limit(requests=20, window=60)  # 20 requests per minute
async def get_security_score(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """Get security score"""
    service = SecurityService(db)
    return await service.get_security_score(current_user.id)
