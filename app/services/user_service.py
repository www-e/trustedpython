"""User service - refactored with SOC."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.exceptions import NotFoundError

from app.services.user_auth import UserAuthService
from app.services.user_profile import UserProfileService
from app.services.user_stats import UserStatsService
from app.services.user_password import UserPasswordService


class UserService:
    """Service for user-related business logic (orchestrator)."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service with focused sub-services.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

        # Sub-services for specific concerns
        self.auth = UserAuthService(db)
        self.profile = UserProfileService(db)
        self.stats = UserStatsService(db)
        self.password = UserPasswordService(db)

    # Core CRUD Operations

    async def get_user(self, user_id: int) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def update_user(
        self,
        user_id: int,
        **kwargs
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
        """
        # Don't allow updating sensitive fields directly
        sensitive_fields = {"password_hash", "id", "created_at"}
        for field in sensitive_fields:
            if field in kwargs:
                del kwargs[field]

        user = await self.user_repo.update(user_id, **kwargs)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    # Delegate methods to sub-services

    async def register(self, user_data: UserCreate) -> User:
        """Register new user - delegates to auth service."""
        return await self.auth.register(user_data)

    async def login(self, phone: str, password: str) -> dict:
        """Authenticate user - delegates to auth service."""
        return await self.auth.login(phone, password)

    async def get_profile(self, user_id: int) -> User:
        """Get user profile - delegates to profile service."""
        return await self.profile.get_profile(user_id)

    async def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        avatar_url: str | None = None,
        bio: str | None = None
    ) -> User:
        """Update user profile - delegates to profile service."""
        return await self.profile.update_profile(user_id, username, avatar_url, bio)

    async def deactivate_user(self, user_id: int) -> User:
        """Deactivate user - delegates to profile service."""
        return await self.profile.deactivate_user(user_id)

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics - delegates to stats service."""
        return await self.stats.get_user_stats(user_id)

    async def get_trade_history(self, user_id: int, limit: int = 20, offset: int = 0) -> list:
        """Get trade history - delegates to stats service."""
        return await self.stats.get_trade_history(user_id, limit, offset)

    async def get_mediators(self, min_rating: float = 0.0, limit: int = 100, offset: int = 0) -> list[User]:
        """Get mediators - delegates to stats service."""
        return await self.stats.get_mediators(min_rating, limit, offset)

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Change password - delegates to password service."""
        return await self.password.change_password(user_id, old_password, new_password)

    async def update_password_v2(self, user_id: int, current_password: str, new_password: str) -> None:
        """Change password (v2) - delegates to password service."""
        return await self.password.change_password(user_id, current_password, new_password)
