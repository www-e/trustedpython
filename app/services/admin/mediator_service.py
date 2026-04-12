"""
Mediator Management Service for admin operations.

Handles all mediator-related admin functionality including listing mediators,
viewing details, verification, tier management, suspension, and application
processing.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.deal import Deal
from app.models.mediator import Mediator, MediatorApplication, MediatorPaymentMethod
from app.models.user import User, UserProfile
from app.schemas.admin import (
    ApplicationPaymentMethod,
    MediatorApplicationItem,
    MediatorApplicationsResponse,
    MediatorInAdminList,
    MediatorListResponse,
    UserInApplication,
)

logger = logging.getLogger(__name__)


class MediatorManagementService:
    """
    Service for managing mediators in the admin dashboard.

    Provides functionality for:
    - Listing and viewing mediator details
    - Verifying mediators
    - Updating mediator tiers
    - Suspending mediators
    - Managing mediator applications
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the mediator management service.

        Args:
            db: Database session for async operations
        """
        self.db = db

    async def list_all_mediators(self, page: int = 1, limit: int = 20) -> MediatorListResponse:
        """
        List all mediators.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            MediatorListResponse: List of mediators
        """
        # Get total count
        total = await self.db.scalar(select(func.count(Mediator.id)))

        # Get mediators
        result = await self.db.execute(
            select(Mediator).join(User).join(UserProfile).offset((page - 1) * limit).limit(limit)
        )

        mediators = result.scalars().all()

        # Transform to response format
        mediator_items = []
        for mediator in mediators:
            # Get deals completed count
            deals_completed = (
                await self.db.scalar(
                    select(func.count(Deal.id)).where(
                        and_(Deal.mediator_id == mediator.user_id, Deal.status == "completed")
                    )
                )
                or 0
            )

            mediator_items.append(
                MediatorInAdminList(
                    id=str(mediator.user_id),
                    username=mediator.user.username,
                    display_name=(
                        mediator.user.profile.display_name if mediator.user.profile else None
                    ),
                    avatar_url=(
                        mediator.user.profile.avatar_url if mediator.user.profile else None
                    ),
                    is_verified=(
                        mediator.user.profile.is_verified if mediator.user.profile else False
                    ),
                    tier=mediator.tier,
                    deals_completed=deals_completed,
                    avg_rating=(
                        float(mediator.user.profile.rating) if mediator.user.profile else 0.0
                    ),
                    is_active=mediator.is_active,
                    created_at=mediator.user.created_at,
                )
            )

        return MediatorListResponse(
            mediators=mediator_items, pagination={"page": page, "limit": limit, "total": total or 0}
        )

    async def get_mediator_details(self, mediator_id: UUID) -> Dict[str, Any]:
        """
        Get mediator details for admin.

        Args:
            mediator_id: Mediator user ID

        Returns:
            Mediator details

        Raises:
            NotFoundException: If mediator not found
        """
        result = await self.db.execute(
            select(Mediator)
            .join(User)
            .join(UserProfile)
            .options(selectinload(Mediator.user), selectinload(Mediator.payment_methods))
            .where(Mediator.user_id == mediator_id)
        )
        mediator = result.scalar_one_or_none()

        if not mediator:
            raise NotFoundException(str(mediator_id), "Mediator")

        # Get deals completed count
        deals_completed = (
            await self.db.scalar(
                select(func.count(Deal.id)).where(
                    and_(Deal.mediator_id == mediator_id, Deal.status == "completed")
                )
            )
            or 0
        )

        return {
            "id": str(mediator.user_id),
            "username": mediator.user.username,
            "display_name": mediator.user.profile.display_name if mediator.user.profile else None,
            "avatar_url": mediator.user.profile.avatar_url if mediator.user.profile else None,
            "email": mediator.user.email,
            "phone": mediator.user.phone,
            "is_verified": mediator.user.profile.is_verified if mediator.user.profile else False,
            "tier": mediator.tier,
            "specialization": mediator.specialization,
            "experience": mediator.experience,
            "bio": mediator.bio,
            "deals_completed": deals_completed,
            "avg_rating": float(mediator.user.profile.rating) if mediator.user.profile else 0.0,
            "response_rate": mediator.response_rate,
            "avg_response_time": mediator.avg_response_time,
            "payment_methods": [
                {"type": pm.method_type, "name": pm.method_name} for pm in mediator.payment_methods
            ],
            "is_active": mediator.is_active,
            "created_at": mediator.user.created_at,
            "verified_at": None,  # This would come from verification history
        }

    async def verify_mediator(
        self, mediator_id: UUID, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a mediator.

        Args:
            mediator_id: Mediator user ID
            notes: Optional admin notes

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If mediator not found
        """
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == mediator_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise NotFoundException(str(mediator_id), "Mediator")

        profile.is_verified = True
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("verify_mediator", mediator_id, notes)

        return {"message": "Mediator verified successfully"}

    async def update_mediator_tier(
        self, mediator_id: UUID, tier: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update mediator's tier.

        Args:
            mediator_id: Mediator user ID
            tier: New tier (bronze, silver, gold, elite)
            reason: Reason for tier change

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If mediator not found
        """
        result = await self.db.execute(select(Mediator).where(Mediator.user_id == mediator_id))
        mediator = result.scalar_one_or_none()

        if not mediator:
            raise NotFoundException(str(mediator_id), "Mediator")

        mediator.tier = tier
        await self.db.commit()

        # Log admin action
        await self._log_admin_action(
            "update_mediator_tier", mediator_id, f"New tier: {tier}, Reason: {reason}"
        )

        return {"message": "Mediator tier updated successfully"}

    async def suspend_mediator(self, mediator_id: UUID) -> Dict[str, Any]:
        """
        Suspend a mediator.

        Args:
            mediator_id: Mediator user ID

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If mediator not found
        """
        result = await self.db.execute(select(Mediator).where(Mediator.user_id == mediator_id))
        mediator = result.scalar_one_or_none()

        if not mediator:
            raise NotFoundException(str(mediator_id), "Mediator")

        mediator.is_active = False
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("suspend_mediator", mediator_id, "Mediator suspended")

        return {"message": "Mediator suspended successfully"}

    async def get_mediator_applications(
        self, status: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> MediatorApplicationsResponse:
        """
        Get mediator applications.

        Args:
            status: Filter by status (pending, approved, rejected)
            page: Page number
            limit: Items per page

        Returns:
            MediatorApplicationsResponse: List of applications
        """
        query = select(MediatorApplication).options(selectinload(MediatorApplication.user))

        if status:
            query = query.where(MediatorApplication.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query.order_by(desc(MediatorApplication.created_at)))
        applications = result.scalars().all()

        # Transform to response format
        application_items = []
        for app in applications:
            application_items.append(
                MediatorApplicationItem(
                    id=str(app.id),
                    user=UserInApplication(
                        id=str(app.user_id),
                        username=app.user.username,
                        display_name=app.user.profile.display_name if app.user.profile else None,
                        avatar_url=app.user.profile.avatar_url if app.user.profile else None,
                    ),
                    specialization=app.specialization,
                    experience=app.experience,
                    payment_methods=[
                        ApplicationPaymentMethod(type=pm.method_type, name=pm.method_name)
                        for pm in app.payment_methods
                    ],
                    bio=app.bio,
                    status=app.status,
                    applied_at=app.created_at,
                )
            )

        return MediatorApplicationsResponse(
            applications=application_items,
            pagination={"page": page, "limit": limit, "total": total or 0},
        )

    async def approve_mediator_application(self, application_id: UUID) -> Dict[str, Any]:
        """
        Approve a mediator application.

        Args:
            application_id: Application ID

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If application not found
        """
        result = await self.db.execute(
            select(MediatorApplication).where(MediatorApplication.id == application_id)
        )
        application = result.scalar_one_or_none()

        if not application:
            raise NotFoundException(str(application_id), "Mediator application")

        application.status = "approved"

        # Create mediator profile
        mediator = Mediator(
            user_id=application.user_id,
            specialization=application.specialization,
            experience=application.experience,
            bio=application.bio,
            is_active=True,
            tier="bronze",
        )
        self.db.add(mediator)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action(
            "approve_mediator_application", application_id, "Application approved"
        )

        return {"message": "Mediator application approved successfully"}

    async def reject_mediator_application(
        self, application_id: UUID, reason: str
    ) -> Dict[str, Any]:
        """
        Reject a mediator application.

        Args:
            application_id: Application ID
            reason: Rejection reason

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If application not found
        """
        result = await self.db.execute(
            select(MediatorApplication).where(MediatorApplication.id == application_id)
        )
        application = result.scalar_one_or_none()

        if not application:
            raise NotFoundException(str(application_id), "Mediator application")

        application.status = "rejected"
        application.rejection_reason = reason
        await self.db.commit()

        # Log admin action
        await self._log_admin_action(
            "reject_mediator_application", application_id, f"Reason: {reason}"
        )

        return {"message": "Mediator application rejected successfully"}

    async def _log_admin_action(
        self, action: str, target_id: UUID, notes: Optional[str] = None
    ) -> None:
        """
        Log admin action for audit trail.

        Args:
            action: Action performed
            target_id: ID of target entity
            notes: Optional notes
        """
        # In production, you would save this to an AuditLog model
        # For now, we'll just log it
        logger.info(f"Admin action: {action} on {target_id} - Notes: {notes}")
