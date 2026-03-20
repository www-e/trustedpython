"""User repository."""

from typing import Optional

from sqlalchemy import select

from app.models.user import User
from app.models.enums import UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self, db):
        """
        Initialize user repository.

        Args:
            db: Database session
        """
        super().__init__(User, db)

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """
        Get a user by phone number.

        Args:
            phone: Phone number

        Returns:
            User instance if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        Get users by role.

        Args:
            role: User role
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user instances
        """
        result = await self.db.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        Get active users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active user instances
        """
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
