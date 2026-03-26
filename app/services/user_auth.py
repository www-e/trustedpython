"""User authentication service."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.schemas.user import UserCreate
from app.exceptions import (
    ConflictError,
    AuthenticationError,
    NotFoundError
)


class UserAuthService:
    """Service for user authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user auth service.

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

    async def verify_password(self, user_id: int, password: str) -> bool:
        """
        Verify user's password.

        Args:
            user_id: User ID
            password: Password to verify

        Returns:
            True if password is correct

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        return verify_password(password, user.password_hash)
