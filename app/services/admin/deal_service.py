"""
Deal Management service for admin operations.

Handles all deal-related admin operations including listing deals,
viewing deal details, resolving disputes, and canceling deals.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.deal import Deal
from app.schemas.admin import DealInAdminList, DealListResponse

logger = logging.getLogger(__name__)


class DealManagementService:
    """
    Deal management service for admin operations.

    Provides comprehensive deal administration functionality including
    deal listing, detail viewing, dispute resolution, and deal cancellation.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize DealManagementService.

        Args:
            db: Database session for async operations
        """
        self.db = db

    async def list_all_deals(
        self, status: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> DealListResponse:
        """
        Get all deals with filtering.

        Args:
            status: Filter by status
            page: Page number
            limit: Items per page

        Returns:
            DealListResponse: List of deals
        """
        query = select(Deal).options(
            selectinload(Deal.account),
            selectinload(Deal.listing),
            selectinload(Deal.buyer),
            selectinload(Deal.seller),
            selectinload(Deal.mediator),
        )

        if status:
            query = query.where(Deal.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query.order_by(desc(Deal.created_at)))
        deals = result.scalars().all()

        # Transform to response format
        deal_items = []
        for deal in deals:
            # Get account/listing title
            account_title = (
                deal.account.title
                if deal.account
                else (deal.listing.title if deal.listing else "Unknown")
            )
            game = (
                deal.account.game if deal.account else (deal.listing.game if deal.listing else None)
            )

            deal_items.append(
                DealInAdminList(
                    id=str(deal.id),
                    status=deal.status,
                    account_title=account_title,
                    price=float(deal.total_amount),
                    buyer_username=deal.buyer.username,
                    seller_username=deal.seller.username,
                    mediator_name=deal.mediator.username if deal.mediator else None,
                    created_at=deal.created_at,
                    is_disputed=deal.status == "disputed",
                )
            )

        return DealListResponse(
            deals=deal_items, pagination={"page": page, "limit": limit, "total": total or 0}
        )

    async def get_deal_details(self, deal_id: UUID) -> Dict[str, Any]:
        """
        Get deal details for admin.

        Args:
            deal_id: Deal ID

        Returns:
            Deal details

        Raises:
            NotFoundException: If deal not found
        """
        result = await self.db.execute(
            select(Deal)
            .options(
                selectinload(Deal.account),
                selectinload(Deal.listing),
                selectinload(Deal.buyer),
                selectinload(Deal.seller),
                selectinload(Deal.mediator),
                selectinload(Deal.payment),
            )
            .where(Deal.id == deal_id)
        )
        deal = result.scalar_one_or_none()

        if not deal:
            raise NotFoundException(str(deal_id), "Deal")

        # Get account/listing details
        account_title = (
            deal.account.title
            if deal.account
            else (deal.listing.title if deal.listing else "Unknown")
        )
        game = deal.account.game if deal.account else (deal.listing.game if deal.listing else None)

        return {
            "id": str(deal.id),
            "status": deal.status,
            "account_id": str(deal.account_id) if deal.account_id else None,
            "listing_id": str(deal.listing_id) if deal.listing_id else None,
            "account_title": account_title,
            "game": game,
            "price": float(deal.total_amount),
            "buyer": {"id": str(deal.buyer_id), "username": deal.buyer.username},
            "seller": {"id": str(deal.seller_id), "username": deal.seller.username},
            "mediator": (
                {"id": str(deal.mediator_id), "username": deal.mediator.username}
                if deal.mediator
                else None
            ),
            "payment_status": deal.payment.status if deal.payment else None,
            "payment_screenshot": deal.payment.screenshot_url if deal.payment else None,
            "chat_room_id": str(deal.chat_room_id) if deal.chat_room_id else None,
            "notes": deal.notes,
            "dispute_reason": None,  # This would come from a dispute field
            "created_at": deal.created_at,
            "updated_at": deal.updated_at,
            "completed_at": deal.completed_at,
        }

    async def resolve_dispute(
        self,
        deal_id: UUID,
        decision: str,
        resolution_notes: str,
        refund_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a disputed deal.

        Args:
            deal_id: Deal ID
            decision: Resolution decision (buyer, seller, refund)
            resolution_notes: Resolution notes
            refund_amount: Refund amount if applicable

        Returns:
            Dict with resolution details

        Raises:
            NotFoundException: If deal not found
        """
        result = await self.db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()

        if not deal:
            raise NotFoundException(str(deal_id), "Deal")

        deal.status = "completed"
        deal.completed_at = datetime.now(timezone.utc)

        # In production, you would handle refunds, notifications, etc.
        await self.db.commit()

        # Log admin action
        await self._log_admin_action(
            "resolve_dispute",
            deal_id,
            f"Decision: {decision}, Notes: {resolution_notes}, Refund: {refund_amount}",
        )

        return {
            "deal_id": str(deal_id),
            "status": "resolved",
            "decision": decision,
            "resolved_at": datetime.now(timezone.utc),
            "resolved_by": "admin",  # This would be the actual admin ID
        }

    async def cancel_deal(self, deal_id: UUID, reason: str) -> Dict[str, Any]:
        """
        Cancel a deal.

        Args:
            deal_id: Deal ID
            reason: Cancellation reason

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If deal not found
        """
        result = await self.db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()

        if not deal:
            raise NotFoundException(str(deal_id), "Deal")

        deal.status = "cancelled"
        deal.cancelled_at = datetime.now(timezone.utc)
        deal.cancellation_reason = reason

        await self.db.commit()

        # Log admin action
        await self._log_admin_action("cancel_deal", deal_id, f"Reason: {reason}")

        return {"message": "Deal cancelled successfully"}

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
