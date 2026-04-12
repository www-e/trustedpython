"""
Payment processing service for the buy flow.

Handles payment submission, confirmation, rejection, and status checking
for account purchase transactions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal import Deal, Payment
from app.schemas.deal import DealStatus, PaymentStatus, PaymentStatusResponse


class PaymentService:
    """Service for payment processing operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize payment service.

        Args:
            db: Async database session
        """
        self.db = db

    async def submit_payment(
        self, deal_id: str, screenshot_url: str, notes: Optional[str] = None
    ) -> PaymentStatusResponse:
        """
        Submit payment screenshot.

        Creates or updates a payment record with the submitted screenshot
        and updates the deal status to PAYMENT_SUBMITTED.

        Args:
            deal_id: Deal ID
            screenshot_url: URL to uploaded screenshot
            notes: Optional notes

        Returns:
            PaymentStatusResponse with payment details

        Raises:
            ValueError: If deal not found
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        # Create or update payment record
        payment = Payment(
            deal_id=deal.id,
            status=PaymentStatus.SUBMITTED,
            screenshot_url=screenshot_url,
            submitted_at=datetime.utcnow(),
            notes=notes,
        )
        self.db.add(payment)

        # Update deal status
        deal.status = DealStatus.PAYMENT_SUBMITTED

        await self.db.commit()

        return PaymentStatusResponse(
            deal_id=str(deal.id),
            status=PaymentStatus.SUBMITTED,
            screenshot_url=screenshot_url,
            submitted_at=payment.submitted_at,
            verified_at=None,
            rejection_reason=None,
        )

    async def confirm_payment(
        self, deal_id: str, notes: Optional[str] = None
    ) -> PaymentStatusResponse:
        """
        Confirm payment (mediator action).

        Verifies the payment screenshot and updates the payment status
        to VERIFIED. Also updates the deal status to VERIFIED.

        Args:
            deal_id: Deal ID
            notes: Optional notes

        Returns:
            PaymentStatusResponse with updated payment details

        Raises:
            ValueError: If deal or payment not found
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        query = query.options(selectinload(Deal.payment))
        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        if not deal.payment:
            raise ValueError("No payment found")

        # Update payment
        deal.payment.status = PaymentStatus.VERIFIED
        deal.payment.verified_at = datetime.utcnow()
        if notes:
            deal.payment.notes = notes

        # Update deal status
        deal.status = DealStatus.VERIFIED

        await self.db.commit()

        return PaymentStatusResponse(
            deal_id=str(deal.id),
            status=PaymentStatus.VERIFIED,
            screenshot_url=deal.payment.screenshot_url,
            submitted_at=deal.payment.submitted_at,
            verified_at=deal.payment.verified_at,
            rejection_reason=None,
        )

    async def reject_payment(self, deal_id: str, reason: str) -> PaymentStatusResponse:
        """
        Reject payment (mediator action).

        Rejects the payment with a reason and updates the payment status
        to REJECTED. Also updates the deal status to REJECTED.

        Args:
            deal_id: Deal ID
            reason: Rejection reason

        Returns:
            PaymentStatusResponse with rejection details

        Raises:
            ValueError: If deal or payment not found
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        query = query.options(selectinload(Deal.payment))
        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        if not deal.payment:
            raise ValueError("No payment found")

        # Update payment
        deal.payment.status = PaymentStatus.REJECTED
        deal.payment.rejection_reason = reason

        # Update deal status
        deal.status = DealStatus.REJECTED

        await self.db.commit()

        return PaymentStatusResponse(
            deal_id=str(deal.id),
            status=PaymentStatus.REJECTED,
            screenshot_url=deal.payment.screenshot_url,
            submitted_at=deal.payment.submitted_at,
            verified_at=None,
            rejection_reason=reason,
        )

    async def check_payment_status(self, deal_id: str) -> PaymentStatusResponse:
        """
        Check payment status.

        Retrieves the current payment status for a deal.

        Args:
            deal_id: Deal ID

        Returns:
            PaymentStatusResponse with current payment status

        Raises:
            ValueError: If deal not found
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        query = query.options(selectinload(Deal.payment))
        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        payment = deal.payment
        if not payment:
            return PaymentStatusResponse(
                deal_id=str(deal.id),
                status=PaymentStatus.PENDING,
                screenshot_url=None,
                submitted_at=None,
                verified_at=None,
                rejection_reason=None,
            )

        return PaymentStatusResponse(
            deal_id=str(deal.id),
            status=PaymentStatus(payment.status) if isinstance(payment.status, str) else payment.status,
            screenshot_url=payment.screenshot_url,
            submitted_at=payment.submitted_at,
            verified_at=payment.verified_at,
            rejection_reason=payment.rejection_reason,
        )
