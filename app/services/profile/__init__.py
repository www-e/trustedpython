"""
Profile services package.

Provides specialized profile services for user profile management and listing operations.
This package maintains backward compatibility through the ProfileService facade.

Usage:
    # Direct import (recommended for new code):
    from app.services.profile import ProfileManagementService, ListingManagementService

    # Facade import (for backward compatibility):
    from app.services.profile import ProfileService
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.profile.listing_management_service import ListingManagementService
from app.services.profile.profile_management_service import ProfileManagementService

__all__ = [
    "ProfileManagementService",
    "ListingManagementService",
    "ProfileService",  # Facade for backward compatibility
]


# Backward compatibility facade
class ProfileService:
    """
    Facade for backward compatibility with legacy ProfileService.

    This class provides the same interface as the original monolithic
    ProfileService by delegating to specialized service modules.

    Deprecated: Import specific services directly instead.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize facade with database session."""
        self.db = db
        self._profile_management: ProfileManagementService | None = None
        self._listing_management: ListingManagementService | None = None

    @property
    def profile_management(self) -> ProfileManagementService:
        """Get profile management service instance."""
        if self._profile_management is None:
            self._profile_management = ProfileManagementService(self.db)
        return self._profile_management

    @property
    def listing_management(self) -> ListingManagementService:
        """Get listing management service instance."""
        if self._listing_management is None:
            self._listing_management = ListingManagementService(self.db)
        return self._listing_management

    # Profile management methods - delegate to profile management service
    async def get_current_profile(self, user_id: Any) -> Any:
        """Get current user's full profile."""
        return await self.profile_management.get_current_profile(user_id)

    async def get_user_stats(self, user_id: Any) -> Any:
        """Get detailed user statistics."""
        return await self.profile_management.get_user_stats(user_id)

    async def get_trade_history(
        self, user_id: Any, status: str | None = None, page: int = 1, limit: int = 20
    ) -> Any:
        """Get user's trade history with pagination."""
        return await self.profile_management.get_trade_history(
            user_id, status=status, page=page, limit=limit
        )

    async def update_profile(self, user_id: Any, data: Any) -> Any:
        """Update user profile."""
        return await self.profile_management.update_profile(user_id, data)

    async def upload_avatar(self, user_id: Any, file_data: bytes, filename: str) -> Any:
        """Upload user avatar."""
        return await self.profile_management.upload_avatar(user_id, file_data, filename)

    async def get_public_profile(self, target_user_id: Any) -> Any:
        """Get public profile of another user."""
        return await self.profile_management.get_public_profile(target_user_id)

    # Listing management methods - delegate to listing management service
    async def get_user_listings(
        self, user_id: Any, status: str | None = None, page: int = 1, limit: int = 20
    ) -> Any:
        """Get user's listings with pagination."""
        return await self.listing_management.get_user_listings(
            user_id, status=status, page=page, limit=limit
        )

    async def create_listing(self, user_id: Any, data: Any) -> Any:
        """Create a new listing."""
        return await self.listing_management.create_listing(user_id, data)

    async def get_listing_details(self, listing_id: Any) -> Any:
        """Get listing details."""
        return await self.listing_management.get_listing_details(listing_id)

    async def update_listing(self, listing_id: Any, user_id: Any, data: Any) -> Any:
        """Update a listing."""
        return await self.listing_management.update_listing(listing_id, user_id, data)

    async def delete_listing(self, listing_id: Any, user_id: Any) -> Any:
        """Delete a listing."""
        return await self.listing_management.delete_listing(listing_id, user_id)

    async def update_listing_status(
        self, listing_id: Any, user_id: Any, status: str
    ) -> Any:
        """Update listing status."""
        return await self.listing_management.update_listing_status(listing_id, user_id, status)

    async def upload_listing_image(self, file_data: bytes, filename: str) -> Any:
        """Upload a listing image."""
        return await self.listing_management.upload_listing_image(file_data, filename)

    # Helper methods - delegate to base utilities
    async def _get_user(self, user_id: Any) -> Any:
        """Get user by ID."""
        from .base import get_user

        return await get_user(self.db, user_id)

    async def _get_profile(self, user_id: Any) -> Any:
        """Get user profile by user ID."""
        from .base import get_profile

        return await get_profile(self.db, user_id)

    async def _get_user_and_profile(self, user_id: Any) -> Any:
        """Get user and profile together."""
        from .base import get_user_and_profile

        return await get_user_and_profile(self.db, user_id)

    async def _get_listing(self, listing_id: Any) -> Any:
        """Get listing by ID."""
        from .base import get_listing

        return await get_listing(self.db, listing_id)

    async def _calculate_user_stats(self, user_id: Any) -> Any:
        """Calculate basic user stats."""
        from .base import calculate_user_stats

        return await calculate_user_stats(self.db, user_id)

    async def _calculate_detailed_stats(self, user_id: Any) -> Any:
        """Calculate detailed user stats."""
        from .base import calculate_detailed_stats

        return await calculate_detailed_stats(self.db, user_id)

    async def _build_trade_history_items(self, deals: Any, user_id: Any) -> Any:
        """Build trade history items from deals."""
        from .base import build_trade_history_items

        return await build_trade_history_items(self.db, deals, user_id)

    async def _check_listing_rate_limit(self, user_id: Any) -> Any:
        """Check if user has exceeded listing creation rate limit."""
        from .base import check_listing_rate_limit

        return await check_listing_rate_limit(self.db, user_id)
