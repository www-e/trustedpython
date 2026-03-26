"""User password management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.core.security import verify_password, hash_password
from app.exceptions import NotFoundError, AuthenticationError, ValidationError


class UserPasswordService:
    """Service for user password management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user password service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Raises:
            NotFoundError: If user not found
            AuthenticationError: If current password is incorrect
            ValidationError: If new password is invalid
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Update password
        password_hash = hash_password(new_password)
        await self.user_repo.update_password(user_id, password_hash)

    async def reset_password(self, user_id: int, new_password: str) -> None:
        """
        Reset user password (admin operation).

        Args:
            user_id: User ID
            new_password: New password

        Raises:
            NotFoundError: If user not found
            ValidationError: If new password is invalid
        """
        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Update password without verifying current password
        password_hash = hash_password(new_password)
        await self.user_repo.update_password(user_id, password_hash)
