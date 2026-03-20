"""User service - business logic layer."""

from typing import Optional
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.schemas.user import UserCreate
from app.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ConflictError
)


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user

        Raises:
            ConflictError: If phone number already exists
            ValidationError: If data is invalid
        """
        # Check if phone already exists
        existing_user = await self.user_repo.get_by_phone(user_data.phone)
        if existing_user:
            raise ConflictError(
                f"User with phone {user_data.phone} already exists"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user = await self.user_repo.create(
            phone=user_data.phone,
            password_hash=password_hash,
            role=user_data.role
        )

        return user

    async def login(self, phone: str, password: str) -> dict:
        """
        Authenticate user and return JWT token.

        Args:
            phone: User's phone number
            password: User's password

        Returns:
            Dictionary with access token and token type

        Raises:
            AuthenticationError: If credentials are invalid
            NotFoundError: If user not found
        """
        # Get user by phone
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise NotFoundError("User not found")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

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

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            AuthenticationError: If old password is incorrect
            ValidationError: If new password is invalid
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Update password
        user = await self.user_repo.update(
            user_id,
            password_hash=new_password_hash
        )

        return user
