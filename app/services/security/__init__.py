"""
Security services package.

Provides specialized services for security-related operations including
password management, two-factor authentication, audit logging, and
account freeze management.

This package maintains backward compatibility through the SecurityService facade.

Usage:
    # Direct import (recommended for new code):
    from app.services.security import PasswordService, TwoFactorService

    # Facade import (for backward compatibility):
    from app.services.security import SecurityService
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.security.account_freeze_service import AccountFreezeService
from app.services.security.audit_service import AuditService
from app.services.security.login_history_service import LoginHistoryService
from app.services.security.password_service import PasswordService
from app.services.security.security_score_service import SecurityScoreService
from app.services.security.two_factor_service import TwoFactorService

__all__ = [
    "PasswordService",
    "TwoFactorService",
    "LoginHistoryService",
    "AuditService",
    "AccountFreezeService",
    "SecurityScoreService",
    "SecurityService",  # Facade for backward compatibility
]


# Backward compatibility facade
class SecurityService:
    """
    Facade for backward compatibility with legacy SecurityService.

    This class provides the same interface as the original monolithic
    SecurityService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize facade with database session.

        Args:
            db: Database session
        """
        self.db = db
        self._password: PasswordService | None = None
        self._two_factor: TwoFactorService | None = None
        self._login_history: LoginHistoryService | None = None
        self._audit: AuditService | None = None
        self._account_freeze: AccountFreezeService | None = None
        self._security_score: SecurityScoreService | None = None

    @property
    def password(self) -> PasswordService:
        """Get password service instance."""
        if self._password is None:
            self._password = PasswordService(self.db)
        return self._password

    @property
    def two_factor(self) -> TwoFactorService:
        """Get two-factor service instance."""
        if self._two_factor is None:
            self._two_factor = TwoFactorService(self.db)
        return self._two_factor

    @property
    def login_history(self) -> LoginHistoryService:
        """Get login history service instance."""
        if self._login_history is None:
            self._login_history = LoginHistoryService(self.db)
        return self._login_history

    @property
    def audit(self) -> AuditService:
        """Get audit service instance."""
        if self._audit is None:
            self._audit = AuditService(self.db)
        return self._audit

    @property
    def account_freeze(self) -> AccountFreezeService:
        """Get account freeze service instance."""
        if self._account_freeze is None:
            self._account_freeze = AccountFreezeService(self.db)
        return self._account_freeze

    @property
    def security_score(self) -> SecurityScoreService:
        """Get security score service instance."""
        if self._security_score is None:
            self._security_score = SecurityScoreService(self.db)
        return self._security_score

    # Password management methods - delegate to password service
    async def change_password(self, user_id: Any, data: Any) -> Any:
        """Change user password."""
        return await self.password.change_password(user_id, data)

    async def logout_all_sessions(self, user_id: Any) -> Any:
        """Logout user from all sessions."""
        return await self.password.logout_all_sessions(user_id)

    # Login history methods - delegate to login history service
    async def get_login_history(
        self,
        user_id: Any,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> Any:
        """Get user's login history."""
        return await self.login_history.get_login_history(user_id, page, page_size, status_filter)

    async def get_security_settings(self, user_id: Any) -> Any:
        """Get user's security settings."""
        return await self.login_history.get_security_settings(user_id)

    async def update_security_settings(self, user_id: Any, data: Any) -> Any:
        """Update user's security settings."""
        return await self.login_history.update_security_settings(user_id, data)

    # Two-factor authentication methods - delegate to 2FA service
    async def enable_2fa(self, user_id: Any, password: str) -> Any:
        """Enable two-factor authentication."""
        return await self.two_factor.enable_2fa(user_id, password)

    async def verify_2fa(self, user_id: Any, code: str) -> Any:
        """Verify 2FA code and complete setup."""
        return await self.two_factor.verify_2fa(user_id, code)

    async def disable_2fa(self, user_id: Any, code: str) -> Any:
        """Disable two-factor authentication."""
        return await self.two_factor.disable_2fa(user_id, code)

    # Audit log methods - delegate to audit service
    async def get_audit_log(
        self,
        user_id: Any,
        page: int = 1,
        page_size: int = 20,
        event_type: str | None = None,
    ) -> Any:
        """Get user's security audit log."""
        return await self.audit.get_audit_log(user_id, page, page_size, event_type)

    async def report_suspicious_activity(
        self,
        user_id: Any,
        activity_type: str,
        description: str,
        evidence: str | None = None,
    ) -> Any:
        """Report suspicious activity."""
        return await self.audit.report_suspicious_activity(
            user_id, activity_type, description, evidence
        )

    # Account freeze methods - delegate to account freeze service
    async def freeze_account(self, user_id: Any, reason: str, duration_hours: int) -> Any:
        """Freeze user account."""
        return await self.account_freeze.freeze_account(user_id, reason, duration_hours)

    async def unfreeze_account(self, user_id: Any) -> Any:
        """Unfreeze user account."""
        return await self.account_freeze.unfreeze_account(user_id)

    # Security score methods - delegate to security score service
    async def get_security_score(self, user_id: Any) -> Any:
        """Calculate and return user's security score."""
        return await self.security_score.get_security_score(user_id)

    # Private method - delegate to base utility
    async def _log_security_event(
        self,
        user_id: Any,
        event_type: str,
        metadata: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log security event to database."""
        from app.services.security.base import log_security_event

        await log_security_event(self.db, user_id, event_type, metadata, ip_address, user_agent)
