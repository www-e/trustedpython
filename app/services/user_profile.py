"""User profile management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.exceptions import NotFoundError, ConflictError


class UserProfileService:
    """Service for user profile management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user profile service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: int) -> User:
        """
        Get user profile.

        Args:
            user_id: User ID

        Returns:
            User profile

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        avatar_url: str | None = None,
        bio: str | None = None
    ) -> User:
        """
        Update user profile fields.

        Args:
            user_id: User ID
            username: New username
            avatar_url: New avatar URL
            bio: New bio

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ConflictError: If username is taken
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        # Check if username is taken
        if username and username != user.username:
            existing = await self.user_repo.get_by_username(username)
            if existing and existing.id != user_id:
                raise ConflictError("Username already taken")

        # Update profile
        user = await self.user_repo.update_profile(
            user_id,
            username=username,
            avatar_url=avatar_url,
            bio=bio
        )

        return user

    async def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            Deactivated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.update(user_id, is_active=False)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
