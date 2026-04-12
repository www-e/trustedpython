"""
Security score calculation service.

Calculates and analyzes user security scores based on various factors.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import SecurityEvent, Session, User
from app.schemas.security import SecurityScoreResponse, SecurityVulnerability
from app.services.security.base import get_active_sessions_count, get_failed_login_count


class SecurityScoreService:
    """
    Service for security score calculation and analysis.

    Provides methods for calculating security scores and identifying vulnerabilities.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize security score service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_security_score(self, user_id: UUID) -> SecurityScoreResponse:
        """
        Calculate and return user's security score.

        Args:
            user_id: ID of the user

        Returns:
            SecurityScoreResponse with score, vulnerabilities, and recommendations

        Raises:
            NotFoundError: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

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
        active_sessions = await get_active_sessions_count(self.db, user_id)

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
        failed_logins = await get_failed_login_count(self.db, user_id, days=7)

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
