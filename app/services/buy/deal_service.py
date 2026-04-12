"""
Deal Management Service for Buy Flow.

Handles deal creation, status updates, retrieval, and chat room management.
Extracted from buy_service.py for better separation of concerns.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.chat import ChatParticipant, ChatRoom
from app.models.deal import Deal
from app.models.mediator import Mediator
from app.models.user import User
from app.schemas.common import PaginationSchema
from app.schemas.deal import (
    AccountFullSchema,
    AccountSummarySchema,
    DealDetailResponse,
    DealResponse,
    DealStatus,
    MediatorSummarySchema,
    PaymentInfoSchema,
    PaymentStatus,
    UserSummarySchema,
)


class BuyDealService:
    """
    Service for managing deals in the buy flow.

    Handles:
    - Deal creation with mediator assignment
    - Deal detail retrieval
    - Deal status updates
    - User deal listing
    - Chat room creation and participant management
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the deal service.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_deal(
        self,
        user_id: str,
        account_id: str,
        mediator_id: str,
        quantity: int = 1,
        notes: Optional[str] = None,
    ) -> DealResponse:
        """
        Create a new deal with mediator assignment.

        This method:
        1. Validates account availability
        2. Validates mediator exists
        3. Creates a chat room for deal communication
        4. Creates the deal record
        5. Adds all participants (buyer, seller, mediator) to the chat room

        Args:
            user_id: Buyer user ID
            account_id: Account ID to purchase
            mediator_id: Mediator ID for transaction oversight
            quantity: Quantity (default: 1)
            notes: Optional notes for the deal

        Returns:
            DealResponse with created deal details

        Raises:
            ValueError: If account not found, not available, or mediator not found
        """
        # Get account
        account_query = select(Account).where(Account.id == uuid.UUID(account_id))
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account or account.status != "active":
            raise ValueError("Account not found or not available")

        # Get mediator
        mediator_query = select(Mediator).where(Mediator.user_id == uuid.UUID(mediator_id))
        mediator_result = await self.db.execute(mediator_query)
        mediator = mediator_result.scalar_one_or_none()

        if not mediator:
            raise ValueError("Mediator not found")

        # Create chat room
        chat_room = ChatRoom(deal_id=None, room_type="deal")  # Will be updated after deal creation
        self.db.add(chat_room)
        await self.db.flush()

        # Create deal
        deal = Deal(
            buyer_id=uuid.UUID(user_id),
            seller_id=account.seller_id,
            mediator_id=uuid.UUID(mediator_id),
            account_id=uuid.UUID(account_id),
            status=DealStatus.PENDING,
            total_amount=account.price * quantity,
            quantity=quantity,
            notes=notes,
            chat_room_id=chat_room.id,
        )
        self.db.add(deal)
        await self.db.flush()

        # Update chat room with deal ID
        chat_room.deal_id = deal.id

        # Add participants to chat room
        buyer_participant = ChatParticipant(
            chat_room_id=chat_room.id, user_id=uuid.UUID(user_id), role="buyer"
        )
        seller_participant = ChatParticipant(
            chat_room_id=chat_room.id, user_id=account.seller_id, role="seller"
        )
        mediator_participant = ChatParticipant(
            chat_room_id=chat_room.id, user_id=uuid.UUID(mediator_id), role="mediator"
        )
        self.db.add_all([buyer_participant, seller_participant, mediator_participant])

        await self.db.commit()

        # Create response
        mediator_user = mediator.user
        mediator_profile = mediator_user.profile if mediator_user else None
        return DealResponse(
            id=str(deal.id),
            status=DealStatus(deal.status) if isinstance(deal.status, str) else deal.status,
            account=AccountSummarySchema(
                id=str(account.id),
                title=account.title,
                price=float(account.price),
                game=account.game,
            ),
            mediator=MediatorSummarySchema(
                id=str(mediator.user_id),
                name=mediator_profile.display_name if mediator_profile and mediator_profile.display_name else "",
                avatar=mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else "",
                rating=float(mediator.rating or 0),
            ),
            buyer_id=str(deal.buyer_id),
            seller_id=str(deal.seller_id),
            total_amount=float(deal.total_amount),
            created_at=deal.created_at,
            chat_room_id=str(chat_room.id),
        )

    async def get_deal_details(self, deal_id: str, user_id: str) -> DealDetailResponse:
        """
        Get detailed deal information with permission check.

        Retrieves comprehensive deal details including:
        - Account information
        - Mediator details
        - Buyer and seller information
        - Payment status
        - Chat room ID
        - Timestamps

        Args:
            deal_id: Deal ID
            user_id: User ID (for permission check - must be buyer or seller)

        Returns:
            DealDetailResponse with full deal details

        Raises:
            ValueError: If deal not found or access denied
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        query = query.options(
            selectinload(Deal.account),
            selectinload(Deal.buyer),
            selectinload(Deal.seller),
            selectinload(Deal.mediator),
            selectinload(Deal.payment),
        )

        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        # Check permission - user must be buyer or seller
        if str(deal.buyer_id) != user_id and str(deal.seller_id) != user_id:
            raise ValueError("Access denied")

        # Build payment info if available
        payment_info = None
        if deal.payment:
            payment_info = PaymentInfoSchema(
                status=PaymentStatus(deal.payment.status) if isinstance(deal.payment.status, str) else deal.payment.status,
                screenshot_url=deal.payment.screenshot_url,
                submitted_at=deal.payment.submitted_at,
                verified_at=deal.payment.verified_at,
                rejection_reason=deal.payment.rejection_reason,
            )

        # Ensure account exists for response
        account = deal.account
        if not account:
            raise ValueError("Deal has no associated account")

        # Build mediator info safely
        deal_mediator = deal.mediator
        mediator_profile = deal_mediator.profile if deal_mediator else None
        mediator_id = str(deal.mediator_id) if deal.mediator_id else ""
        mediator_name = mediator_profile.display_name if mediator_profile and mediator_profile.display_name else ""
        mediator_avatar = mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else ""

        # Build buyer/seller info safely
        buyer_profile = deal.buyer.profile if deal.buyer else None
        seller_profile = deal.seller.profile if deal.seller else None

        return DealDetailResponse(
            id=str(deal.id),
            status=DealStatus(deal.status) if isinstance(deal.status, str) else deal.status,
            account=AccountFullSchema(
                id=str(account.id),
                title=account.title,
                game=account.game,
                price=float(account.price),
                images=[img.url for img in account.images],
            ),
            mediator=MediatorSummarySchema(
                id=mediator_id,
                name=mediator_name,
                avatar=mediator_avatar,
                rating=0.0,
            ),
            buyer=UserSummarySchema(
                id=str(deal.buyer.id),
                username=deal.buyer.username,
                display_name=buyer_profile.display_name if buyer_profile else None,
            ),
            seller=UserSummarySchema(
                id=str(deal.seller.id),
                username=deal.seller.username,
                display_name=seller_profile.display_name if seller_profile else None,
            ),
            total_amount=float(deal.total_amount),
            payment=payment_info,
            chat_room_id=str(deal.chat_room_id),
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            completed_at=deal.completed_at,
            notes=deal.notes,
        )

    async def update_deal_status(
        self, deal_id: str, status: DealStatus, notes: Optional[str] = None
    ) -> DealResponse:
        """
        Update deal status with optional notes.

        Updates the deal status and optionally adds notes.
        If status is COMPLETED, automatically sets completed_at timestamp.

        Args:
            deal_id: Deal ID
            status: New status from DealStatus enum
            notes: Optional notes to append to deal

        Returns:
            DealResponse with updated deal details

        Raises:
            ValueError: If deal not found

        Note:
            Valid status transitions should be validated at the API level
            before calling this method.
        """
        query = select(Deal).where(Deal.id == uuid.UUID(deal_id))
        result = await self.db.execute(query)
        deal = result.scalar_one_or_none()

        if not deal:
            raise ValueError("Deal not found")

        deal.status = status
        if notes:
            deal.notes = notes

        # Set completion timestamp if deal is completed
        if status == DealStatus.COMPLETED:
            deal.completed_at = datetime.utcnow()

        await self.db.commit()

        # Return updated deal
        return await self._get_deal_response(deal.id)

    async def get_user_deals(
        self,
        user_id: str,
        role: Optional[str] = None,
        status: Optional[DealStatus] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get deals for a user with filtering and pagination.

        Retrieves deals where the user is either buyer or seller,
        with optional filtering by role and status.

        Args:
            user_id: User ID
            role: Filter by role (buyer/seller) - if None, returns both
            status: Filter by deal status
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Dict containing:
            - deals: List of DealResponse objects
            - pagination: Pagination info (page, limit, total, total_pages)

        Note:
            Results are ordered by created_at descending (newest first).
        """
        query = select(Deal)

        # Apply role filter
        if role == "buyer":
            query = query.where(Deal.buyer_id == uuid.UUID(user_id))
        elif role == "seller":
            query = query.where(Deal.seller_id == uuid.UUID(user_id))
        else:
            # Get all deals where user is buyer OR seller
            query = query.where(
                or_(Deal.buyer_id == uuid.UUID(user_id), Deal.seller_id == uuid.UUID(user_id))
            )

        # Apply status filter
        if status:
            query = query.where(Deal.status == status)

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(Deal.created_at.desc())

        # Execute query with relationships
        query = query.options(selectinload(Deal.account), selectinload(Deal.mediator))
        result = await self.db.execute(query)
        deals = result.scalars().all()

        # Convert to response schemas
        deal_responses = []
        for deal in deals:
            deal_mediator = deal.mediator
            mediator_profile = deal_mediator.profile if deal_mediator else None
            account = deal.account
            deal_responses.append(
                DealResponse(
                    id=str(deal.id),
                    status=DealStatus(deal.status) if isinstance(deal.status, str) else deal.status,
                    account=AccountSummarySchema(
                        id=str(account.id) if account else "",
                        title=account.title if account else "",
                        price=float(account.price) if account else 0.0,
                        game=account.game if account else "",
                    ),
                    mediator=MediatorSummarySchema(
                        id=str(deal.mediator_id) if deal.mediator_id else "",
                        name=mediator_profile.display_name if mediator_profile and mediator_profile.display_name else "",
                        avatar=mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else "",
                        rating=0.0,
                    ),
                    buyer_id=str(deal.buyer_id),
                    seller_id=str(deal.seller_id),
                    total_amount=float(deal.total_amount),
                    created_at=deal.created_at,
                    chat_room_id=str(deal.chat_room_id),
                )
            )

        # Create pagination metadata
        pagination = PaginationSchema.create(page=page, limit=limit, total=total)

        return {
            "deals": deal_responses,
            "pagination": {
                "page": pagination.page,
                "limit": pagination.limit,
                "total": pagination.total,
                "total_pages": pagination.total_pages,
            },
        }

    async def _get_deal_response(self, deal_id: uuid.UUID) -> DealResponse:
        """
        Helper method to build DealResponse from deal ID.

        Internal method used to retrieve deal details and format
        them into a DealResponse schema.

        Args:
            deal_id: Deal UUID

        Returns:
            DealResponse with deal details

        Raises:
            NoResultFound: If deal not found (internal use, expected to exist)
        """
        query = select(Deal).where(Deal.id == deal_id)
        query = query.options(selectinload(Deal.account), selectinload(Deal.mediator))
        result = await self.db.execute(query)
        deal = result.scalar_one()

        deal_mediator = deal.mediator
        mediator_profile = deal_mediator.profile if deal_mediator else None
        account = deal.account

        return DealResponse(
            id=str(deal.id),
            status=DealStatus(deal.status) if isinstance(deal.status, str) else deal.status,
            account=AccountSummarySchema(
                id=str(account.id) if account else "",
                title=account.title if account else "",
                price=float(account.price) if account else 0.0,
                game=account.game if account else "",
            ),
            mediator=MediatorSummarySchema(
                id=str(deal.mediator_id) if deal.mediator_id else "",
                name=mediator_profile.display_name if mediator_profile and mediator_profile.display_name else "",
                avatar=mediator_profile.avatar_url if mediator_profile and mediator_profile.avatar_url else "",
                rating=0.0,
            ),
            buyer_id=str(deal.buyer_id),
            seller_id=str(deal.seller_id),
            total_amount=float(deal.total_amount),
            created_at=deal.created_at,
            chat_room_id=str(deal.chat_room_id),
        )
