"""
Buy services package.

Provides specialized services for the buy flow including account browsing,
mediator selection, deal management, and payment processing.

Usage:
    # Direct import (recommended for new code):
    from app.services.buy import AccountBrowsingService, BuyMediatorService

    # Facade import (for backward compatibility):
    from app.services.buy import BuyService
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.account import (
    AccountDetailResponse,
    AccountsBrowseResponse,
    SimilarAccountsResponse,
)
from app.schemas.deal import (
    DealDetailResponse,
    DealResponse,
    DealStatus,
    PaymentStatusResponse,
)
from app.schemas.mediator import MediatorDetailResponse, MediatorReviewsResponse
from app.services.buy.account_browsing_service import AccountBrowsingService
from app.services.buy.deal_service import BuyDealService
from app.services.buy.mediator_service import BuyMediatorService
from app.services.buy.payment_service import PaymentService

__all__ = [
    "AccountBrowsingService",
    "BuyMediatorService",
    "BuyDealService",
    "PaymentService",
    "BuyService",  # Facade for backward compatibility
]


# Backward compatibility facade
class BuyService:
    """
    Facade for backward compatibility with legacy BuyService.

    This class provides the same interface as the original monolithic
    BuyService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize facade with database session."""
        self.db = db
        self._accounts: AccountBrowsingService | None = None
        self._mediators: BuyMediatorService | None = None
        self._deals: BuyDealService | None = None
        self._payments: PaymentService | None = None

    @property
    def accounts(self) -> AccountBrowsingService:
        """Get account browsing service instance."""
        if self._accounts is None:
            self._accounts = AccountBrowsingService(self.db)
        return self._accounts

    @property
    def mediators(self) -> BuyMediatorService:
        """Get mediator service instance."""
        if self._mediators is None:
            self._mediators = BuyMediatorService(self.db)
        return self._mediators

    @property
    def deals(self) -> BuyDealService:
        """Get deal service instance."""
        if self._deals is None:
            self._deals = BuyDealService(self.db)
        return self._deals

    @property
    def payments(self) -> PaymentService:
        """Get payment service instance."""
        if self._payments is None:
            self._payments = PaymentService(self.db)
        return self._payments

    # Account browsing methods - delegate to account service
    async def browse_accounts(
        self,
        game: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        level: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> AccountsBrowseResponse:
        """Browse and filter available accounts."""
        return await self.accounts.browse_accounts(
            game=game,
            price_min=price_min,
            price_max=price_max,
            level=level,
            search=search,
            sort=sort,
            page=page,
            limit=limit,
        )

    async def get_account_details(self, account_id: str) -> AccountDetailResponse:
        """Get detailed account information."""
        return await self.accounts.get_account_details(account_id)

    async def get_similar_accounts(
        self, account_id: str, limit: int = 5
    ) -> SimilarAccountsResponse:
        """Get similar accounts."""
        return await self.accounts.get_similar_accounts(account_id, limit)

    # Mediator methods - delegate to mediator service
    async def list_mediators(
        self,
        specialization: str | None = None,
        sort: str = "rating",
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List available mediators."""
        return await self.mediators.list_mediators(
            specialization=specialization,
            sort=sort,
            page=page,
            limit=limit,
        )

    async def get_mediator_details(self, mediator_id: str) -> MediatorDetailResponse:
        """Get detailed mediator information."""
        return await self.mediators.get_mediator_details(mediator_id)

    async def get_mediator_reviews(
        self, mediator_id: str, page: int = 1, limit: int = 10
    ) -> MediatorReviewsResponse:
        """Get mediator reviews."""
        return await self.mediators.get_mediator_reviews(mediator_id, page, limit)

    # Deal methods - delegate to deal service
    async def create_deal(
        self,
        user_id: str,
        account_id: str,
        mediator_id: str,
        quantity: int = 1,
        notes: str | None = None,
    ) -> DealResponse:
        """Create a new deal."""
        return await self.deals.create_deal(
            user_id=user_id,
            account_id=account_id,
            mediator_id=mediator_id,
            quantity=quantity,
            notes=notes,
        )

    async def get_deal_details(
        self, deal_id: str, user_id: str
    ) -> DealDetailResponse:
        """Get detailed deal information."""
        return await self.deals.get_deal_details(deal_id, user_id)

    async def update_deal_status(
        self,
        deal_id: str,
        status: DealStatus,
        notes: str | None = None,
    ) -> DealResponse:
        """Update deal status."""
        return await self.deals.update_deal_status(deal_id, status, notes)

    async def get_user_deals(
        self,
        user_id: str,
        role: str | None = None,
        status: DealStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get current user's deals."""
        return await self.deals.get_user_deals(
            user_id=user_id,
            role=role,
            status=status,
            page=page,
            limit=limit,
        )

    # Payment methods - delegate to payment service
    async def submit_payment(
        self,
        deal_id: str,
        screenshot_url: str,
        notes: str | None = None,
    ) -> PaymentStatusResponse:
        """Submit payment screenshot."""
        return await self.payments.submit_payment(
            deal_id=deal_id,
            screenshot_url=screenshot_url,
            notes=notes,
        )

    async def confirm_payment(
        self,
        deal_id: str,
        notes: str | None = None,
    ) -> PaymentStatusResponse:
        """Confirm payment receipt."""
        return await self.payments.confirm_payment(deal_id, notes)

    async def reject_payment(
        self, deal_id: str, reason: str
    ) -> PaymentStatusResponse:
        """Reject payment."""
        return await self.payments.reject_payment(deal_id, reason)

    async def check_payment_status(
        self, deal_id: str
    ) -> PaymentStatusResponse:
        """Check payment status."""
        return await self.payments.check_payment_status(deal_id)
