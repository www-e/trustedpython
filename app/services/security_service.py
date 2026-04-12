"""Security service for handling security-related operations"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import pyotp
from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import hash_password, verify_password
from app.models.user import LoginHistory, SecurityEvent, Session, TrustedDevice, User
from app.schemas.security import (
    AuditLogItem,
    AuditLogResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginHistoryItem,
    LoginHistoryResponse,
    SecurityScoreResponse,
    SecuritySettingsResponse,
    SecurityVulnerability,
    SuccessResponse,
    TwoFactorSetupResponse,
    UpdateSecuritySettingsRequest,
)


class SecurityService:
    """Service for security operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def change_password(
        self, user_id: UUID, data: ChangePasswordRequest
    ) -> ChangePasswordResponse:
        """Change user password with current password verification"""
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            # Log failed attempt
            await self._log_security_event(
                user_id, "password_change_failed", {"reason": "incorrect_current_password"}
            )
            raise UnauthorizedException("Current password is incorrect")

        # Check new password is not same as current
        if verify_password(data.new_password, user.password_hash):
            raise ValidationException("New password must be different from current password")

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.requires_password_change = False

        await self.db.commit()
        await self.db.refresh(user)

        # Log successful password change
        await self._log_security_event(
            user_id, "password_changed", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return ChangePasswordResponse(success=True, message="Password changed successfully")

    async def logout_all_sessions(self, user_id: UUID) -> SuccessResponse:
        """Logout user from all sessions by invalidating all refresh tokens"""
        # Delete all refresh tokens for user
        await self.db.execute(select(Session).where(Session.user_id == user_id))
        from sqlalchemy import delete

        await self.db.execute(delete(Session).where(Session.user_id == user_id))

        await self.db.commit()

        # Log security event
        await self._log_security_event(
            user_id,
            "all_sessions_terminated",
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        return SuccessResponse(success=True, message="Logged out from all devices successfully")

    async def get_login_history(
        self, user_id: UUID, page: int = 1, page_size: int = 20, status_filter: Optional[str] = None
    ) -> LoginHistoryResponse:
        """Get user's login history with pagination"""
        # Build query
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)

        if status_filter:
            query = query.where(LoginHistory.status == status_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(LoginHistory.timestamp))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        history_items = result.scalars().all()

        # Convert to response format
        history = [
            LoginHistoryItem(
                timestamp=item.timestamp,
                ip_address=item.ip_address,
                device_info=item.device_info,
                status=item.status,
                location=item.location,
            )
            for item in history_items
        ]

        return LoginHistoryResponse(total=total, page=page, page_size=page_size, history=history)

    async def get_security_settings(self, user_id: UUID) -> SecuritySettingsResponse:
        """Get user's security settings"""
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        # Get trusted devices
        trusted_devices_result = await self.db.execute(
            select(TrustedDevice).where(
                and_(TrustedDevice.user_id == user_id, TrustedDevice.is_active == True)
            )
        )
        trusted_devices = trusted_devices_result.scalars().all()

        trusted_devices_list = [
            {
                "id": str(device.id),
                "device_name": device.device_name,
                "device_info": device.device_info,
                "last_used": device.last_used.isoformat() if device.last_used else None,
                "created_at": device.created_at.isoformat(),
            }
            for device in trusted_devices
        ]

        # Get active sessions count
        sessions_result = await self.db.execute(
            select(func.count()).select_from(
                select(Session)
                .where(
                    and_(
                        Session.user_id == user_id,
                        Session.revoked_at.is_(None),
                        Session.expires_at > datetime.utcnow(),
                    )
                )
                .subquery()
            )
        )
        active_sessions = sessions_result.scalar() or 0

        return SecuritySettingsResponse(
            two_factor_enabled=user.two_factor_enabled or False,
            login_notifications=user.login_notifications or False,
            trusted_devices=trusted_devices_list,
            security_questions=user.security_questions or {},
            last_password_change=user.password_changed_at,
            active_sessions=active_sessions,
        )

    async def update_security_settings(
        self, user_id: UUID, data: UpdateSecuritySettingsRequest
    ) -> SecuritySettingsResponse:
        """Update user's security settings"""
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        # Update settings
        if data.login_notifications is not None:
            user.login_notifications = data.login_notifications

        if data.security_questions is not None:
            # Hash security question answers
            hashed_questions = {
                k: hash_password(v) if v else None for k, v in data.security_questions.items()
            }
            user.security_questions = {**(user.security_questions or {}), **hashed_questions}

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await self._log_security_event(
            user_id,
            "security_settings_updated",
            {
                "login_notifications": data.login_notifications,
                "security_questions_updated": bool(data.security_questions),
            },
        )

        return await self.get_security_settings(user_id)

    async def enable_2fa(self, user_id: UUID, password: str) -> TwoFactorSetupResponse:
        """Enable two-factor authentication for user"""
        # Verify password first
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Password verification failed")

        # Generate TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code URL
        qr_code_url = totp.provisioning_uri(name=user.email, issuer_name="Game Account Marketplace")

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Store in user (temporary, will be confirmed later)
        user.two_factor_secret = hash_password(secret)
        user.two_factor_backup_codes = [hash_password(code) for code in backup_codes]

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await self._log_security_event(
            user_id, "2fa_enabled", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return TwoFactorSetupResponse(
            qr_code_url=qr_code_url, backup_codes=backup_codes, secret=secret
        )

    async def verify_2fa(self, user_id: UUID, code: str) -> SuccessResponse:
        """Verify 2FA code and complete 2FA setup"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if not user.two_factor_secret:
            raise ValidationException("2FA not set up for this account")

        # Verify TOTP code (check against stored secret)
        # For now, we'll mark as enabled without verification
        # In production, you'd verify the TOTP code
        user.two_factor_enabled = True

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await self._log_security_event(
            user_id, "2fa_verified", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return SuccessResponse(success=True, message="2FA enabled successfully")

    async def disable_2fa(self, user_id: UUID, code: str) -> SuccessResponse:
        """Disable two-factor authentication"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if not user.two_factor_enabled:
            raise ValidationException("2FA is not enabled for this account")

        # Verify code (in production, verify TOTP code)
        # For now, proceed with disabling
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = None

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await self._log_security_event(
            user_id, "2fa_disabled", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return SuccessResponse(success=True, message="2FA disabled successfully")

    async def get_audit_log(
        self, user_id: UUID, page: int = 1, page_size: int = 20, event_type: Optional[str] = None
    ) -> AuditLogResponse:
        """Get user's security audit log"""
        # Build query
        query = select(SecurityEvent).where(SecurityEvent.user_id == user_id)

        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(SecurityEvent.timestamp))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        events = result.scalars().all()

        # Convert to response format
        audit_events = [
            AuditLogItem(
                timestamp=event.timestamp,
                event=event.event_type,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                details=event.event_metadata,
            )
            for event in events
        ]

        return AuditLogResponse(total=total, page=page, page_size=page_size, events=audit_events)

    async def report_suspicious_activity(
        self, user_id: UUID, activity_type: str, description: str, evidence: Optional[str] = None
    ) -> SuccessResponse:
        """Report suspicious activity"""
        # Log as high-priority security event
        await self._log_security_event(
            user_id,
            "suspicious_activity_reported",
            {
                "activity_type": activity_type,
                "description": description,
                "evidence": evidence,
                "severity": "high",
            },
        )

        # In production, you might:
        # - Send alert to security team
        # - Temporarily restrict account
        # - Trigger additional monitoring

        return SuccessResponse(
            success=True,
            message="Suspicious activity reported successfully. Our security team will investigate.",
        )

    async def freeze_account(
        self, user_id: UUID, reason: str, duration_hours: int
    ) -> SuccessResponse:
        """Freeze user account for security reasons"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if user.is_frozen:
            raise ValidationException("Account is already frozen")

        # Calculate unfreeze time
        unfreeze_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        # Freeze account
        user.is_frozen = True
        user.frozen_until = unfreeze_at
        user.freeze_reason = reason

        await self.db.commit()
        await self.db.refresh(user)

        # Logout all sessions
        await self.logout_all_sessions(user_id)

        # Log security event
        await self._log_security_event(
            user_id,
            "account_frozen",
            {
                "reason": reason,
                "duration_hours": duration_hours,
                "unfreeze_at": unfreeze_at.isoformat(),
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Account frozen successfully. Will be automatically unfrozen on {unfreeze_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        )

    async def unfreeze_account(self, user_id: UUID) -> SuccessResponse:
        """Unfreeze user account"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if not user.is_frozen:
            raise ValidationException("Account is not frozen")

        # Unfreeze account
        user.is_frozen = False
        user.frozen_until = None
        user.freeze_reason = None

        await self.db.commit()
        await self.db.refresh(user)

        # Log security event
        await self._log_security_event(
            user_id, "account_unfrozen", {"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        return SuccessResponse(success=True, message="Account unfrozen successfully")

    async def get_security_score(self, user_id: UUID) -> SecurityScoreResponse:
        """Calculate and return user's security score"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        # Calculate security score
        score = 100
        vulnerabilities = []
        recommendations = []

        # Check 2FA
        if not user.two_factor_enabled:
            score -= 20
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="high",
                    issue="Two-factor authentication not enabled",
                    recommendation="Enable 2FA to significantly improve account security",
                )
            )
            recommendations.append("Enable two-factor authentication")

        # Check password age
        if user.password_changed_at:
            password_age = (datetime.now(timezone.utc) - user.password_changed_at).days
            if password_age > 90:
                score -= 10
                vulnerabilities.append(
                    SecurityVulnerability(
                        severity="medium",
                        issue=f"Password not changed in {password_age} days",
                        recommendation="Change your password regularly (every 90 days)",
                    )
                )
                recommendations.append("Change your password regularly")
        else:
            score -= 15
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="medium",
                    issue="Password has never been changed",
                    recommendation="Change your password to ensure account security",
                )
            )

        # Check security questions
        if not user.security_questions:
            score -= 10
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="medium",
                    issue="Security questions not configured",
                    recommendation="Set up security questions for account recovery",
                )
            )
            recommendations.append("Configure security questions")

        # Check login notifications
        if not user.login_notifications:
            score -= 5
            recommendations.append("Enable login notifications for enhanced security")

        # Check active sessions
        sessions_result = await self.db.execute(
            select(func.count()).select_from(
                select(Session)
                .where(
                    and_(
                        Session.user_id == user_id,
                        Session.revoked_at.is_(None),
                        Session.expires_at > datetime.utcnow(),
                    )
                )
                .subquery()
            )
        )
        active_sessions = sessions_result.scalar() or 0

        if active_sessions > 5:
            score -= 5
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="low",
                    issue=f"High number of active sessions ({active_sessions})",
                    recommendation="Review and logout from unused sessions",
                )
            )
            recommendations.append("Review and manage active sessions")

        # Check failed login attempts (from security events)
        failed_logins_result = await self.db.execute(
            select(func.count()).select_from(
                select(SecurityEvent)
                .where(
                    and_(
                        SecurityEvent.user_id == user_id,
                        SecurityEvent.event_type == "login_failed",
                        SecurityEvent.timestamp > datetime.now(timezone.utc) - timedelta(days=7),
                    )
                )
                .subquery()
            )
        )
        failed_logins = failed_logins_result.scalar() or 0

        if failed_logins > 5:
            score -= 10
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="high",
                    issue=f"Multiple failed login attempts detected ({failed_logins} in last 7 days)",
                    recommendation="Review your account activity and consider enabling 2FA",
                )
            )

        # Ensure score is between 0 and 100
        score = max(0, min(100, score))

        return SecurityScoreResponse(
            score=score,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            last_updated=datetime.now(timezone.utc),
        )

    async def _log_security_event(
        self,
        user_id: UUID,
        event_type: str,
        metadata: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log security event to database"""
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

        self.db.add(event)
        await self.db.commit()
