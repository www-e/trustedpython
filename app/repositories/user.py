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

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            User instance if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        avatar_url: str | None = None,
        bio: str | None = None
    ) -> Optional[User]:
        """
        Update user profile fields.

        Args:
            user_id: User ID
            username: New username
            avatar_url: New avatar URL
            bio: New bio

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if not user:
            return None

        if username is not None:
            user.username = username
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if bio is not None:
            user.bio = bio

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_password(
        self,
        user_id: int,
        password_hash: str
    ) -> Optional[User]:
        """
        Update user password.

        Args:
            user_id: User ID
            password_hash: New password hash

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if not user:
            return None

        user.password_hash = password_hash
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def increment_stats(
        self,
        user_id: int,
        completed_deals: int = 0,
        total_deals_as_buyer: int = 0,
        total_deals_as_seller: int = 0
    ) -> Optional[User]:
        """
        Increment user deal statistics.

        Args:
            user_id: User ID
            completed_deals: Number to add to completed deals
            total_deals_as_buyer: Number to add to buyer deals
            total_deals_as_seller: Number to add to seller deals

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if not user:
            return None

        user.completed_deals += completed_deals
        user.total_deals_as_buyer += total_deals_as_buyer
        user.total_deals_as_seller += total_deals_as_seller

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_rating(
        self,
        user_id: int,
        new_rating: float
    ) -> Optional[User]:
        """
        Update user rating.

        Args:
            user_id: User ID
            new_rating: New rating value

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if not user:
            return None

        user.rating = new_rating
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_mediators(
        self,
        min_rating: float = 0.0,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        Get mediator users with optional rating filter.

        Args:
            min_rating: Minimum rating
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of mediator users
        """
        result = await self.db.execute(
            select(User)
            .where(
                User.role == UserRole.MEDIATOR,
                User.is_active == True,
                User.rating >= min_rating
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
