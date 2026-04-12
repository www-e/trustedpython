"""
Admin services package.

Provides specialized admin services for platform management.
This package maintains backward compatibility through the AdminService facade.

Usage:
    # Direct import (recommended for new code):
    from app.services.admin import UserManagementService, DashboardService

    # Facade import (for backward compatibility):
    from app.services.admin import AdminService
"""

from typing import Any

from app.services.admin.audit_service import AuditService
from app.services.admin.content_service import ContentService
from app.services.admin.dashboard_service import DashboardService
from app.services.admin.deal_service import DealManagementService
from app.services.admin.listing_service import ListingModerationService
from app.services.admin.mediator_service import MediatorManagementService
from app.services.admin.report_service import ReportService
from app.services.admin.user_service import UserManagementService

__all__ = [
    "DashboardService",
    "UserManagementService",
    "ListingModerationService",
    "DealManagementService",
    "MediatorManagementService",
    "ReportService",
    "ContentService",
    "AuditService",
    "AdminService",  # Facade for backward compatibility
]


# Backward compatibility facade
class AdminService:
    """
    Facade for backward compatibility with legacy AdminService.

    This class provides the same interface as the original monolithic
    AdminService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: Any) -> None:
        """Initialize facade with database session."""
        self.db = db
        self._dashboard: DashboardService | None = None
        self._users: UserManagementService | None = None
        self._listings: ListingModerationService | None = None
        self._deals: DealManagementService | None = None
        self._mediators: MediatorManagementService | None = None
        self._reports: ReportService | None = None
        self._content: ContentService | None = None
        self._audit: AuditService | None = None

    @property
    def dashboard(self) -> DashboardService:
        """Get dashboard service instance."""
        if self._dashboard is None:
            self._dashboard = DashboardService(self.db)
        return self._dashboard

    @property
    def users(self) -> UserManagementService:
        """Get user management service instance."""
        if self._users is None:
            self._users = UserManagementService(self.db)
        return self._users

    @property
    def listings(self) -> ListingModerationService:
        """Get listing moderation service instance."""
        if self._listings is None:
            self._listings = ListingModerationService(self.db)
        return self._listings

    @property
    def deals(self) -> DealManagementService:
        """Get deal management service instance."""
        if self._deals is None:
            self._deals = DealManagementService(self.db)
        return self._deals

    @property
    def mediators(self) -> MediatorManagementService:
        """Get mediator management service instance."""
        if self._mediators is None:
            self._mediators = MediatorManagementService(self.db)
        return self._mediators

    @property
    def reports(self) -> ReportService:
        """Get report service instance."""
        if self._reports is None:
            self._reports = ReportService(self.db)
        return self._reports

    @property
    def content(self) -> ContentService:
        """Get content management service instance."""
        if self._content is None:
            self._content = ContentService(self.db)
        return self._content

    @property
    def audit(self) -> AuditService:
        """Get audit service instance."""
        if self._audit is None:
            self._audit = AuditService(self.db)
        return self._audit

    # Dashboard methods - delegate to dashboard service
    async def get_dashboard_stats(self) -> Any:
        """Get dashboard statistics."""
        return await self.dashboard.get_dashboard_stats()

    async def get_analytics(self, period: str = "week") -> Any:
        """Get analytics data."""
        return await self.dashboard.get_analytics(period)

    # User management methods - delegate to user service
    async def list_all_users(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> Any:
        """List all users."""
        return await self.users.list_all_users(page=page, limit=limit, status=status, search=search)

    async def get_user_details(self, user_id: Any) -> Any:
        """Get user details."""
        return await self.users.get_user_details(user_id)

    async def verify_user(self, user_id: Any, notes: str | None = None) -> Any:
        """Verify a user."""
        return await self.users.verify_user(user_id, notes)

    async def suspend_user(
        self, user_id: Any, reason: str, duration_days: int | None = None
    ) -> Any:
        """Suspend a user."""
        return await self.users.suspend_user(user_id, reason, duration_days)

    async def unsuspend_user(self, user_id: Any) -> Any:
        """Unsuspend a user."""
        return await self.users.unsuspend_user(user_id)

    async def ban_user(self, user_id: Any, reason: str) -> Any:
        """Ban a user."""
        return await self.users.ban_user(user_id, reason)

    async def search_users(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Any:
        """Search users."""
        return await self.users.search_users(query, page, limit)

    # Listing moderation methods - delegate to listing service
    async def get_pending_listings(self, page: int = 1, limit: int = 20) -> Any:
        """Get pending listings."""
        return await self.listings.get_pending_listings(page, limit)

    async def approve_listing(self, listing_id: Any, notes: str | None = None) -> Any:
        """Approve a listing."""
        return await self.listings.approve_listing(listing_id, notes)

    async def reject_listing(self, listing_id: Any, reason: str) -> Any:
        """Reject a listing."""
        return await self.listings.reject_listing(listing_id, reason)

    async def remove_listing(self, listing_id: Any) -> Any:
        """Remove a listing."""
        return await self.listings.remove_listing(listing_id)

    # Deal management methods - delegate to deal service
    async def list_all_deals(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
    ) -> Any:
        """List all deals."""
        return await self.deals.list_all_deals(status=status, page=page, limit=limit)

    async def get_deal_details(self, deal_id: Any) -> Any:
        """Get deal details."""
        return await self.deals.get_deal_details(deal_id)

    async def resolve_dispute(
        self,
        deal_id: Any,
        decision: str,
        resolution_notes: str,
        refund_amount: float | None = None,
    ) -> Any:
        """Resolve a dispute."""
        return await self.deals.resolve_dispute(deal_id, decision, resolution_notes, refund_amount)

    async def cancel_deal(self, deal_id: Any, reason: str) -> Any:
        """Cancel a deal."""
        return await self.deals.cancel_deal(deal_id, reason)

    # Mediator management methods - delegate to mediator service
    async def list_all_mediators(self, page: int = 1, limit: int = 20) -> Any:
        """List all mediators."""
        return await self.mediators.list_all_mediators(page, limit)

    async def get_mediator_details(self, mediator_id: Any) -> Any:
        """Get mediator details."""
        return await self.mediators.get_mediator_details(mediator_id)

    async def verify_mediator(self, mediator_id: Any, notes: str | None = None) -> Any:
        """Verify a mediator."""
        return await self.mediators.verify_mediator(mediator_id, notes)

    async def update_mediator_tier(self, mediator_id: Any, tier: str) -> Any:
        """Update mediator tier."""
        return await self.mediators.update_mediator_tier(mediator_id, tier)

    async def suspend_mediator(self, mediator_id: Any) -> Any:
        """Suspend a mediator."""
        return await self.mediators.suspend_mediator(mediator_id)

    async def get_mediator_applications(
        self,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """Get mediator applications."""
        return await self.mediators.get_mediator_applications(status=status, page=page, limit=limit)

    async def approve_mediator_application(self, application_id: Any) -> Any:
        """Approve mediator application."""
        return await self.mediators.approve_mediator_application(application_id)

    async def reject_mediator_application(self, application_id: Any, reason: str) -> Any:
        """Reject mediator application."""
        return await self.mediators.reject_mediator_application(application_id, reason)

    # Report methods - delegate to report service
    async def get_reports(
        self,
        status: str | None = None,
        type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """Get reports."""
        return await self.reports.get_reports(status=status, type=type, page=page, limit=limit)

    async def get_report_details(self, report_id: Any) -> Any:
        """Get report details."""
        return await self.reports.get_report_details(report_id)

    async def resolve_report(
        self, report_id: Any, action: str, notes: str
    ) -> Any:
        """Resolve a report."""
        return await self.reports.resolve_report(report_id, action, notes)

    async def get_blocked_users(self, page: int = 1, limit: int = 20) -> Any:
        """Get blocked users."""
        return await self.reports.get_blocked_users(page, limit)

    async def unblock_user(self, user_id: Any) -> Any:
        """Unblock a user."""
        return await self.reports.unblock_user(user_id)

    # Content management methods - delegate to content service
    async def manage_games(self) -> Any:
        """Manage games."""
        return await self.content.manage_games()

    async def add_game(
        self,
        name: str,
        slug: str,
        icon_url: str | None = None,
        is_popular: bool = False,
    ) -> Any:
        """Add a game."""
        return await self.content.add_game(name, slug, icon_url, is_popular)

    async def update_game(
        self,
        game_id: Any,
        name: str | None = None,
        slug: str | None = None,
        icon_url: str | None = None,
        is_active: bool | None = None,
        is_popular: bool | None = None,
    ) -> Any:
        """Update a game."""
        return await self.content.update_game(game_id, name, slug, icon_url, is_active, is_popular)

    async def manage_categories(self) -> Any:
        """Manage categories."""
        return await self.content.manage_categories()

    async def add_category(
        self, name: str, slug: str, icon: str | None = None, description: str | None = None
    ) -> Any:
        """Add a category."""
        return await self.content.add_category(name, slug, icon, description)

    async def manage_promo_banners(self) -> Any:
        """Manage promo banners."""
        return await self.content.manage_promo_banners()

    async def create_promo_banner(
        self,
        title: str,
        image_url: str,
        subtitle: str | None = None,
        action_url: str | None = None,
        action_text: str | None = None,
        priority: int = 0,
    ) -> Any:
        """Create a promo banner."""
        return await self.content.create_promo_banner(
            title, image_url, subtitle, action_url, action_text, priority
        )

    async def manage_faq(self) -> Any:
        """Manage FAQ."""
        return await self.content.manage_faq()

    async def add_faq_item(
        self, question: str, answer: str, category: str | None = None, display_order: int = 0
    ) -> Any:
        """Add an FAQ item."""
        return await self.content.add_faq_item(question, answer, category, display_order)
