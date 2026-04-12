"""
Buy Mediator Service - Focused mediator functionality.

Handles mediator listing, details, reviews, and statistics
for the buy flow.
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal import Deal
from app.models.mediator import Mediator, MediatorBadge
from app.models.review import Review
from app.schemas.common import PaginationSchema
from app.schemas.mediator import (
    MediatorBadgeSchema,
    MediatorDetailResponse,
    MediatorResponse,
    MediatorReviewSchema,
    MediatorReviewsResponse,
    MediatorStatsSchema,
    MediatorTier,
)


class BuyMediatorService:
    """Service for Buy Flow mediator operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_mediators(
        self,
        specialization: Optional[str] = None,
        sort: str = "rating",
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List available mediators.

        Args:
            specialization: Filter by game specialization
            sort: Sort order (rating, transactions, tier)
            page: Page number
            limit: Items per page

        Returns:
            Dict with mediators list and pagination
        """
        query = select(Mediator).where(Mediator.is_active == True)

        if specialization:
            query = query.where(Mediator.specialization.ilike(f"%{specialization}%"))

        # Apply sorting
        if sort == "transactions":
            query = query.order_by(Mediator.transactions_count.desc())
        elif sort == "tier":
            query = query.order_by(Mediator.tier.desc())
        else:  # rating
            query = query.order_by(Mediator.rating.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        query = query.options(selectinload(Mediator.badges))
        result = await self.db.execute(query)
        mediators = result.scalars().all()

        # Convert to response
        mediator_responses = []
        for mediator in mediators:
            mediator_user = mediator.user
            mediator_profile = mediator_user.profile if mediator_user else None
            mediator_responses.append(
                MediatorResponse(
                    id=str(mediator.user_id),
                    name=mediator_profile.display_name if mediator_profile and mediator_profile.display_name else "",
                    avatar=mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else "",
                    rating=float(mediator.rating or 0),
                    program_rating=float(mediator.program_rating or 0),
                    transactions_count=mediator.transactions_count or 0,
                    specialization=mediator.specialization or "",
                    payment_methods=[],  # TODO: Implement payment methods
                    response_time=self._format_response_time(mediator.avg_response_time),
                    is_online=mediator.is_online,
                    tier=MediatorTier(mediator.tier) if mediator.tier else MediatorTier.BRONZE,
                    is_verified=mediator.is_verified,
                    badges=[
                        MediatorBadgeSchema(
                            id=str(badge.id),
                            name=badge.name,
                            icon=badge.icon,
                            description=badge.description or "",
                            earned_at=badge.earned_at,
                        )
                        for badge in mediator.badges
                    ],
                    bio=mediator.bio or "",
                )
            )

        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return {
            "mediators": mediator_responses,
            "pagination": {
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
                "total_pages": pagination.total_pages,
            },
        }

    async def get_mediator_details(self, mediator_id: str) -> MediatorDetailResponse:
        """
        Get detailed mediator information.

        Args:
            mediator_id: Mediator ID

        Returns:
            MediatorDetailResponse
        """
        query = select(Mediator).where(Mediator.user_id == uuid.UUID(mediator_id))
        query = query.options(selectinload(Mediator.badges))

        result = await self.db.execute(query)
        mediator = result.scalar_one_or_none()

        if not mediator:
            raise ValueError("Mediator not found")

        # Calculate stats
        stats = await self._get_mediator_stats(mediator_id)

        mediator_user = mediator.user
        mediator_profile = mediator_user.profile if mediator_user else None

        return MediatorDetailResponse(
            id=str(mediator.user_id),
            name=mediator_profile.display_name if mediator_profile and mediator_profile.display_name else "",
            avatar=mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else "",
            rating=float(mediator.rating or 0),
            program_rating=float(mediator.program_rating or 0),
            transactions_count=mediator.transactions_count or 0,
            success_rate=float(stats.get("success_rate", 0)),
            specialization=mediator.specialization or "",
            payment_methods=[],  # TODO: Implement payment methods
            response_time=self._format_response_time(mediator.avg_response_time),
            is_online=mediator.is_online,
            tier=MediatorTier(mediator.tier) if mediator.tier else MediatorTier.BRONZE,
            is_verified=mediator.is_verified,
            badges=[
                MediatorBadgeSchema(
                    id=str(badge.id),
                    name=badge.name,
                    icon=badge.icon,
                    description=badge.description or "",
                    earned_at=badge.earned_at,
                )
                for badge in mediator.badges
            ],
            bio=mediator.bio or "",
            stats=MediatorStatsSchema(
                total_deals=stats.get("total_deals", 0),
                successful_deals=stats.get("successful_deals", 0),
                failed_deals=stats.get("failed_deals", 0),
                success_rate=float(stats.get("success_rate", 0)),
                avg_response_time=float(mediator.avg_response_time or 0),
                member_since=mediator.created_at,
            ),
        )

    async def get_mediator_reviews(
        self, mediator_id: str, page: int = 1, limit: int = 20
    ) -> MediatorReviewsResponse:
        """
        Get reviews for a mediator.

        Args:
            mediator_id: Mediator ID
            page: Page number
            limit: Items per page

        Returns:
            MediatorReviewsResponse
        """
        query = select(Review).where(Review.reviewee_id == uuid.UUID(mediator_id))
        query = query.order_by(Review.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        reviews = result.scalars().all()

        # Convert to response
        review_responses = []
        for review in reviews:
            review_responses.append(
                MediatorReviewSchema(
                    id=str(review.id),
                    reviewer={
                        "username": review.reviewer.username,
                        "avatar": (
                            review.reviewer.profile.avatar_url if review.reviewer.profile else None
                        ),
                    },
                    rating=review.rating,
                    comment=review.comment or "",
                    deal_id=str(review.deal_id),
                    created_at=review.created_at,
                )
            )

        # Get average rating
        avg_query = select(func.avg(Review.rating)).where(
            Review.reviewee_id == uuid.UUID(mediator_id)
        )
        avg_result = await self.db.execute(avg_query)
        avg_rating = float(avg_result.scalar_one() or 0)

        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return MediatorReviewsResponse(
            reviews=review_responses,
            pagination={
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
            },
            average_rating=avg_rating,
        )

    async def _get_mediator_stats(self, mediator_id: str) -> Dict[str, Any]:
        """
        Calculate mediator statistics.

        Args:
            mediator_id: Mediator ID

        Returns:
            Dict with mediator statistics
        """
        # Get deal stats
        deal_query = select(func.count(Deal.id), func.sum(Deal.status == "completed"))
        # TODO: Implement proper stats calculation
        return {"total_deals": 0, "successful_deals": 0, "failed_deals": 0, "success_rate": 0}

    def _format_response_time(self, minutes: Optional[int]) -> str:
        """
        Format response time for display.

        Args:
            minutes: Response time in minutes

        Returns:
            Formatted response time string
        """
        if minutes is None:
            return "N/A"
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}min"
