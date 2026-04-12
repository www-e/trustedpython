"""
Base utilities and shared functionality for profile services.

This module provides common helper functions used across all profile service modules.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.deal import Deal
from app.models.listing import Listing
from app.models.user import User, UserProfile
from app.schemas.profile import TradeHistoryCounterparty, TradeHistoryItem


async def get_user(db: AsyncSession, user_id: UUID) -> User:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User: User object

    Raises:
        NotFoundError: If user not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def get_profile(db: AsyncSession, user_id: UUID) -> UserProfile:
    """
    Get user profile by user ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        UserProfile: User profile object

    Raises:
        NotFoundError: If profile not found
    """
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("User profile not found")
    return profile


async def get_user_and_profile(db: AsyncSession, user_id: UUID) -> tuple[User, UserProfile]:
    """
    Get user and profile together.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Tuple of (User, UserProfile)

    Raises:
        NotFoundError: If user or profile not found
    """
    result = await db.execute(
        select(User, UserProfile)
        .join(UserProfile, User.id == UserProfile.user_id)
        .where(User.id == user_id)
    )
    row = result.first()
    if not row:
        raise NotFoundError("User not found")
    user, profile = row
    return user, profile


async def get_listing(db: AsyncSession, listing_id: UUID) -> Listing:
    """
    Get listing by ID.

    Args:
        db: Database session
        listing_id: Listing ID

    Returns:
        Listing: Listing object

    Raises:
        NotFoundError: If listing not found
    """
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundError("Listing not found")
    return listing


async def calculate_user_stats(db: AsyncSession, user_id: UUID) -> dict:
    """
    Calculate basic user stats.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict with basic stats: completed_deals, accounts_sold, bought_count
    """
    # Count completed deals as buyer
    bought_result = await db.execute(
        select(func.count(Deal.id)).where(
            and_(Deal.buyer_id == user_id, Deal.status == "completed")
        )
    )
    bought_count = bought_result.scalar() or 0

    # Count completed deals as seller
    sold_result = await db.execute(
        select(func.count(Deal.id)).where(
            and_(Deal.seller_id == user_id, Deal.status == "completed")
        )
    )
    accounts_sold = sold_result.scalar() or 0

    # Total completed deals
    completed_deals = bought_count + accounts_sold

    return {
        "completed_deals": completed_deals,
        "accounts_sold": accounts_sold,
        "bought_count": bought_count,
    }


async def calculate_detailed_stats(db: AsyncSession, user_id: UUID) -> dict:
    """
    Calculate detailed user stats.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict with detailed stats including revenue, avg_deal_value, success_rate
    """
    basic_stats = await calculate_user_stats(db, user_id)

    # Calculate total revenue (as seller)
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Deal.total_amount), 0)).where(
            and_(Deal.seller_id == user_id, Deal.status == "completed")
        )
    )
    total_revenue = revenue_result.scalar() or 0

    # Calculate average deal value
    completed_deals = basic_stats["completed_deals"]
    avg_deal_value = float(total_revenue) / completed_deals if completed_deals > 0 else None

    # Calculate success rate (completed / total deals)
    total_deals_result = await db.execute(
        select(func.count(Deal.id)).where(or_(Deal.buyer_id == user_id, Deal.seller_id == user_id))
    )
    total_deals = total_deals_result.scalar() or 0
    success_rate = (completed_deals / total_deals * 100) if total_deals > 0 else 100.0

    return {
        **basic_stats,
        "total_revenue": float(total_revenue) if total_revenue else None,
        "avg_deal_value": avg_deal_value,
        "success_rate": round(success_rate, 2),
        "response_time_avg": None,  # TODO: Calculate from chat response times
    }


async def build_trade_history_items(
    db: AsyncSession, deals: Sequence[Deal], user_id: UUID
) -> List[TradeHistoryItem]:
    """
    Build trade history items from deals.

    Args:
        db: Database session
        deals: List of Deal objects
        user_id: Current user ID

    Returns:
        List of TradeHistoryItem objects
    """
    items = []

    for deal in deals:
        # Determine role and counterparty
        if deal.buyer_id == user_id:
            role = "buyer"
            counterparty_id = deal.seller_id
        else:
            role = "seller"
            counterparty_id = deal.buyer_id

        # Get counterparty info
        counterparty_result = await db.execute(
            select(User, UserProfile)
            .join(UserProfile, User.id == UserProfile.user_id)
            .where(User.id == counterparty_id)
        )
        counterparty_data = counterparty_result.first()

        if counterparty_data:
            counterparty_user, counterparty_profile = counterparty_data
            counterparty = TradeHistoryCounterparty(
                username=counterparty_user.username, avatar_url=counterparty_profile.avatar_url
            )
        else:
            counterparty = TradeHistoryCounterparty(username="Unknown User", avatar_url=None)

        # Get title from listing or account
        title = (
            deal.listing.title if deal.listing else deal.account.title if deal.account else "Trade"
        )

        items.append(
            TradeHistoryItem(
                id=deal.id,
                title=title,
                price=float(deal.total_amount),
                status=deal.status,
                timestamp=deal.created_at,
                game=deal.listing.game if deal.listing else None,
                counterparty=counterparty,
                role=role,
            )
        )

    return items


async def check_listing_rate_limit(db: AsyncSession, user_id: UUID) -> None:
    """
    Check if user has exceeded listing creation rate limit.

    Args:
        db: Database session
        user_id: User ID

    Raises:
        ValidationError: If rate limit exceeded (max 10 listings per day)
    """
    from app.core.exceptions import ValidationError

    # Count listings created in last 24 hours
    since = datetime.utcnow() - timedelta(days=1)

    count_result = await db.execute(
        select(func.count(Listing.id)).where(
            and_(Listing.seller_id == user_id, Listing.created_at >= since)
        )
    )
    count = count_result.scalar() or 0

    if count >= 10:
        raise ValidationError("Rate limit exceeded: Maximum 10 listings per day")
