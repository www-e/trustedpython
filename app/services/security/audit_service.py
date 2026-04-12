"""
Audit logging service.

Handles security event logging and audit trail management.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SecurityEvent
from app.schemas.security import AuditLogItem, AuditLogResponse, SuccessResponse
from app.services.security.base import log_security_event


class AuditService:
    """
    Service for audit logging and security event tracking.

    Provides methods for retrieving audit logs and reporting suspicious activity.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_audit_log(
        self, user_id: UUID, page: int = 1, page_size: int = 20, event_type: Optional[str] = None
    ) -> AuditLogResponse:
        """
        Get user's security audit log.

        Args:
            user_id: ID of the user
            page: Page number
            page_size: Items per page
            event_type: Optional event type filter

        Returns:
            AuditLogResponse with paginated audit events
        """
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
                details=dict(event.event_metadata) if event.event_metadata else None,
            )
            for event in events
        ]

        return AuditLogResponse(total=total, page=page, page_size=page_size, events=audit_events)

    async def report_suspicious_activity(
        self, user_id: UUID, activity_type: str, description: str, evidence: Optional[str] = None
    ) -> SuccessResponse:
        """
        Report suspicious activity.

        Args:
            user_id: ID of the user reporting
            activity_type: Type of suspicious activity
            description: Description of the activity
            evidence: Optional evidence (screenshots, logs, etc.)

        Returns:
            SuccessResponse with report confirmation

        Note:
            In production, this might:
            - Send alert to security team
            - Temporarily restrict account
            - Trigger additional monitoring
        """
        # Log as high-priority security event
        await log_security_event(
            self.db,
            user_id,
            "suspicious_activity_reported",
            {
                "activity_type": activity_type,
                "description": description,
                "evidence": evidence,
                "severity": "high",
            },
        )

        return SuccessResponse(
            success=True,
            message="Suspicious activity reported successfully. Our security team will investigate.",
        )
