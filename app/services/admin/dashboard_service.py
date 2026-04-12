"""
Dashboard and Analytics service for admin platform management.

Handles dashboard statistics, analytics reporting, and platform metrics
including user growth, deal volume, top games, mediator performance,
and revenue trends.
"""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal
from app.models.listing import Listing
from app.models.mediator import Mediator
from app.models.user import User, UserProfile
from app.schemas.admin import (
    AnalyticsResponse,
    DashboardStatsResponse,
    DealVolumeData,
    RevenueTrendData,
    TopGameData,
    TopMediatorData,
    UserGrowthData,
)


class DashboardService:
    """
    Dashboard service for platform analytics and statistics.

    Provides comprehensive dashboard functionality for tracking platform
    metrics, user growth, deal volume, top performing games and mediators,
    and revenue trends.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize DashboardService.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_dashboard_stats(self) -> DashboardStatsResponse:
        """
        Get dashboard overview statistics.

        Returns:
            DashboardStatsResponse: Platform statistics

        Raises:
            ForbiddenException: If user is not admin
        """
        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=32)).replace(day=1)

        # User statistics
        total_users = await self.db.scalar(select(func.count(User.id)))
        active_today = await self.db.scalar(
            select(func.count(User.id)).where(
                User.last_login_at >= today.replace(hour=0, minute=0, second=0)
            )
        )
        new_this_week = await self.db.scalar(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        verified_users = await self.db.scalar(
            select(func.count(UserProfile.id)).where(UserProfile.is_verified == True)
        )
        suspended_users = await self.db.scalar(
            select(func.count(User.id)).where(User.is_suspended == True)
        )

        # Listing statistics
        total_listings = await self.db.scalar(select(func.count(Listing.id)))
        active_listings = await self.db.scalar(
            select(func.count(Listing.id)).where(Listing.status == "active")
        )
        pending_listings = await self.db.scalar(
            select(func.count(Listing.id)).where(Listing.status == "pending")
        )
        sold_this_week = await self.db.scalar(
            select(func.count(Listing.id)).where(
                and_(Listing.status == "sold", Listing.updated_at >= week_ago)
            )
        )

        # Deal statistics
        total_deals = await self.db.scalar(select(func.count(Deal.id)))
        active_deals = await self.db.scalar(
            select(func.count(Deal.id)).where(
                Deal.status.in_(["pending", "awaiting_payment", "payment_submitted"])
            )
        )
        completed_this_week = await self.db.scalar(
            select(func.count(Deal.id)).where(
                and_(Deal.status == "completed", Deal.completed_at >= week_ago)
            )
        )
        disputed_deals = await self.db.scalar(
            select(func.count(Deal.id)).where(Deal.status == "disputed")
        )
        success_rate = 94.5  # This should be calculated from historical data

        # Mediator statistics
        total_mediators = await self.db.scalar(select(func.count(Mediator.id)))
        active_mediators = await self.db.scalar(
            select(func.count(Mediator.id)).where(Mediator.is_active == True)
        )
        verified_mediators = await self.db.scalar(
            select(func.count(UserProfile.id))
            .join(User)
            .join(Mediator)
            .where(UserProfile.is_verified == True)
        )
        avg_response_time = "8 min"  # This should be calculated from actual mediator response times

        # Revenue statistics (platform fees)
        # This would typically come from a separate revenue table or payment processing records
        this_month_revenue = 125000.00
        last_month_revenue = 98000.00
        growth_percentage = (
            ((this_month_revenue - last_month_revenue) / last_month_revenue) * 100
            if last_month_revenue > 0
            else 0
        )

        return DashboardStatsResponse(
            users={
                "total": total_users or 0,
                "active_today": active_today or 0,
                "new_this_week": new_this_week or 0,
                "verified": verified_users or 0,
                "suspended": suspended_users or 0,
            },
            listings={
                "total": total_listings or 0,
                "active": active_listings or 0,
                "pending_approval": pending_listings or 0,
                "sold_this_week": sold_this_week or 0,
            },
            deals={
                "total": total_deals or 0,
                "active": active_deals or 0,
                "completed_this_week": completed_this_week or 0,
                "disputed": disputed_deals or 0,
                "success_rate": success_rate,
            },
            mediators={
                "total": total_mediators or 0,
                "active": active_mediators or 0,
                "verified": verified_mediators or 0,
                "avg_response_time": avg_response_time,
            },
            revenue={
                "this_month": this_month_revenue,
                "last_month": last_month_revenue,
                "growth_percentage": round(growth_percentage, 2),
            },
        )

    async def get_analytics(self, period: str = "week") -> AnalyticsResponse:
        """
        Get detailed analytics for a time period.

        Args:
            period: Time period (day, week, month, year)

        Returns:
            AnalyticsResponse: Detailed analytics data

        Raises:
            ForbiddenException: If user is not admin
        """
        # Determine date range based on period
        today = datetime.now(timezone.utc)
        if period == "day":
            start_date = today - timedelta(days=1)
            date_trunc = "hour"
        elif period == "week":
            start_date = today - timedelta(days=7)
            date_trunc = "day"
        elif period == "month":
            start_date = today - timedelta(days=30)
            date_trunc = "day"
        else:  # year
            start_date = today - timedelta(days=365)
            date_trunc = "month"

        # User growth data
        user_growth = await self._get_user_growth(start_date, period)

        # Deal volume data
        deal_volume = await self._get_deal_volume(start_date, period)

        # Top games
        top_games = await self._get_top_games(start_date)

        # Top mediators
        top_mediators = await self._get_top_mediators(start_date)

        # Revenue trend
        revenue_trend = await self._get_revenue_trend(start_date, period)

        return AnalyticsResponse(
            user_growth=user_growth,
            deal_volume=deal_volume,
            top_games=top_games,
            top_mediators=top_mediators,
            revenue_trend=revenue_trend,
        )

    async def _get_user_growth(
        self, start_date: datetime, period: str
    ) -> List[UserGrowthData]:
        """Get user growth data."""
        # This is a simplified version - in production, you'd use date truncation
        user_growth = []
        for i in range(7 if period in ["day", "week"] else 30):
            date = start_date + timedelta(days=i)
            new_users = (
                await self.db.scalar(
                    select(func.count(User.id)).where(func.date(User.created_at) == date.date())
                )
                or 0
            )
            active_users = (
                await self.db.scalar(
                    select(func.count(User.id)).where(func.date(User.last_login_at) == date.date())
                )
                or 0
            )

            user_growth.append(
                UserGrowthData(
                    date=date.strftime("%Y-%m-%d"),
                    new_users=new_users,
                    active_users=active_users,
                )
            )

        return user_growth

    async def _get_deal_volume(
        self, start_date: datetime, period: str
    ) -> List[DealVolumeData]:
        """Get deal volume data."""
        deal_volume = []
        for i in range(7 if period in ["day", "week"] else 30):
            date = start_date + timedelta(days=i)
            deals = (
                await self.db.scalar(
                    select(func.count(Deal.id)).where(func.date(Deal.created_at) == date.date())
                )
                or 0
            )
            completed = (
                await self.db.scalar(
                    select(func.count(Deal.id)).where(
                        and_(
                            func.date(Deal.completed_at) == date.date(), Deal.status == "completed"
                        )
                    )
                )
                or 0
            )

            deal_volume.append(
                DealVolumeData(
                    date=date.strftime("%Y-%m-%d"), deals=deals, completed=completed
                )
            )

        return deal_volume

    async def _get_top_games(self, start_date: datetime) -> List[TopGameData]:
        """Get top performing games."""
        # Query games with most listings and deals
        result = await self.db.execute(
            select(
                Listing.game,
                func.count(Listing.id).label("listings"),
                func.count(Deal.id).label("deals"),
            )
            .outerjoin(Deal, Listing.id == Deal.listing_id)
            .where(Listing.created_at >= start_date)
            .group_by(Listing.game)
            .order_by(desc("listings"))
            .limit(10)
        )

        top_games = []
        for row in result:
            top_games.append(
                TopGameData(
                    game=row.game or "Unknown", listings=row.listings, deals=row.deals
                )
            )

        return top_games

    async def _get_top_mediators(self, start_date: datetime) -> List[TopMediatorData]:
        """Get top performing mediators."""
        result = await self.db.execute(
            select(
                User.id,
                User.username,
                func.count(Deal.id).label("deals_completed"),
                func.avg(UserProfile.rating).label("avg_rating"),
            )
            .join(Deal, User.id == Deal.mediator_id)
            .join(UserProfile, User.id == UserProfile.user_id)
            .where(Deal.status == "completed", Deal.completed_at >= start_date)
            .group_by(User.id, User.username)
            .order_by(desc("deals_completed"))
            .limit(10)
        )

        top_mediators = []
        for row in result:
            top_mediators.append(
                TopMediatorData(
                    id=str(row.id),
                    name=row.username,
                    deals_completed=row.deals_completed,
                    avg_rating=float(row.avg_rating) if row.avg_rating else 0.0,
                )
            )

        return top_mediators

    async def _get_revenue_trend(
        self, start_date: datetime, period: str
    ) -> List[RevenueTrendData]:
        """Get revenue trend data."""
        # This is a simplified version - in production, calculate from actual revenue
        revenue_trend = []
        for i in range(7 if period in ["day", "week"] else 30):
            date = start_date + timedelta(days=i)
            # In production, this would come from actual revenue calculations
            amount = 5000 + (i * 100) + (hash(date.date()) % 1000)

            revenue_trend.append(
                RevenueTrendData(date=date.strftime("%Y-%m-%d"), amount=amount)
            )

        return revenue_trend
