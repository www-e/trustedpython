"""
Authentication business logic service.

Handles user registration, login, password reset, token management,
and authentication-related operations.
"""

import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User, UserProfile


class AuthService:
    """
    Authentication service for user management operations.

    Provides methods for registration, login, password reset,
    token refresh, and user profile retrieval.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize auth service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def register(self, data: dict) -> dict:
        """
        Register a new user account.

        Args:
            data: Registration data with username, email, phone, password

        Returns:
            dict: Created user with tokens

        Raises:
            ConflictException: If username/email/phone already exists
            ValidationException: If validation fails
        """
        username: str = data.get("username") or ""
        email: str = data.get("email") or ""
        phone: str | None = data.get("phone")
        password: str = data.get("password") or ""

        # Check if username exists
        existing_user = await self._get_user_by_username(username)
        if existing_user:
            raise ConflictException("username", username)

        # Check if email exists
        existing_email = await self._get_user_by_email(email)
        if existing_email:
            raise ConflictException("email", email)

        # Check if phone exists
        if phone:
            existing_phone = await self._get_user_by_phone(phone)
            if existing_phone:
                raise ConflictException("phone", phone)

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=password_hash,
            is_email_verified=False,
            is_active=True,
            is_suspended=False,
        )

        self.db.add(user)
        await self.db.flush()

        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            display_name=username,
            user_role="Trader",
            is_verified=False,
            member_since=datetime.utcnow().date(),
            completed_deals=0,
            rating=0.00,
            accounts_sold=0,
            bought_count=0,
            total_revenue=0.00,
        )

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        tokens = self._generate_tokens(user.id)

        # TODO: Queue background task to send verification email

        return {"user": self._user_to_response(user), **tokens}

    async def login(self, data: dict) -> dict:
        """
        Authenticate user with username/email and password.

        Args:
            data: Login data with username and password

        Returns:
            dict: Authenticated user with tokens

        Raises:
            UnauthorizedException: If credentials are invalid
            ForbiddenException: If account is suspended/deactivated
        """
        username: str = data.get("username") or ""
        password: str = data.get("password") or ""

        # Find user by username or email
        user = await self._get_user_by_username_or_email(username)

        if not user:
            raise UnauthorizedException("Invalid credentials")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid credentials")

        # Check if account is active
        if not user.is_active:
            raise ForbiddenException("Account is deactivated")

        # Check if account is suspended
        if user.is_suspended:
            reason = user.suspension_reason or "Account suspended"
            raise ForbiddenException(reason)

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # Generate tokens
        tokens = self._generate_tokens(user.id)

        return {"user": self._user_to_response(user), **tokens}

    async def forgot_password(self, email: str) -> None:
        """
        Send password reset link to email.

        Args:
            email: User's email address

        Raises:
            NotFoundException: If email not found
        """
        user = await self._get_user_by_email(email)

        if not user:
            # Don't reveal if email exists or not (security best practice)
            # But we need to raise for consistent API behavior
            raise NotFoundException(email, "Email")

        # Generate reset token
        reset_token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

        # TODO: Store token in Redis/DB with expiry (1 hour)
        # TODO: Queue background task to send reset email

        # For now, just acknowledge
        return None

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using token from email.

        Args:
            token: Password reset token
            new_password: New password

        Raises:
            ValidationException: If token is invalid or expired
        """
        # TODO: Verify token from Redis/DB
        # TODO: Check token expiry

        # For now, this is a placeholder
        # In production, you would:
        # 1. Look up token in Redis/DB
        # 2. Verify it's not expired
        # 3. Get user_id from token
        # 4. Update password

        raise ValidationException("Password reset not implemented yet", "token")

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            dict: New tokens

        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")

        if not payload:
            raise UnauthorizedException("Invalid refresh token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid refresh token")
        user_id = UUID(user_id_str)

        # Verify user exists and is active
        user = await self._get_user_by_id(user_id)

        if not user or not user.is_active:
            raise UnauthorizedException("Invalid refresh token")

        # Generate new tokens
        tokens = self._generate_tokens(user.id)

        return tokens

    async def get_current_user(self, user_id: UUID) -> dict:
        """
        Get current user profile with statistics.

        Args:
            user_id: User UUID

        Returns:
            dict: User profile with stats

        Raises:
            NotFoundException: If user not found
        """
        user = await self._get_user_by_id(user_id)

        if not user:
            raise NotFoundException(str(user_id), "User")

        return self._user_to_full_response(user)

    async def verify_email(self, token: str) -> None:
        """
        Verify user email address.

        Args:
            token: Email verification token

        Raises:
            ValidationException: If token is invalid or expired
        """
        # TODO: Verify token from Redis/DB
        # TODO: Check token expiry
        # TODO: Update user.is_email_verified = True
        # TODO: Set user.email_verified_at = datetime.utcnow()

        raise ValidationException("Email verification not implemented yet", "token")

    async def logout(self, user_id: UUID, access_token: str) -> None:
        """
        Logout user by invalidating their session.

        Args:
            user_id: User UUID
            access_token: Access token to invalidate

        Returns:
            None
        """
        # TODO: Add token to Redis blacklist
        # TODO: Set expiry to match token expiration
        # TODO: Update session.revoked_at in database

        return None

    # Helper Methods

    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by UUID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone."""
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def _get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        result = await self.db.execute(
            select(User).where((User.username == identifier) | (User.email == identifier))
        )
        return result.scalar_one_or_none()

    def _generate_tokens(self, user_id: UUID) -> dict:
        """
        Generate JWT access and refresh tokens.

        Args:
            user_id: User UUID

        Returns:
            dict: Tokens with expiration
        """
        access_token = create_access_token({"sub": str(user_id)})
        refresh_token = create_refresh_token({"sub": str(user_id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,  # 1 hour in seconds
        }

    def _user_to_response(self, user: User) -> dict:
        """
        Convert User model to basic response dict.

        Args:
            user: User model instance

        Returns:
            dict: User response data
        """
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "display_name": user.profile.display_name if user.profile else user.username,
            "created_at": user.created_at,
        }

    def _user_to_full_response(self, user: User) -> dict:
        """
        Convert User model to full response dict with stats.

        Args:
            user: User model instance

        Returns:
            dict: Full user response data
        """
        profile = user.profile

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "display_name": profile.display_name if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "is_verified": profile.is_verified if profile else False,
            "created_at": user.created_at,
            "stats": {
                "total_sales": profile.accounts_sold if profile else 0,
                "total_purchases": profile.bought_count if profile else 0,
                "rating": float(profile.rating) if profile else 0.0,
                "reviews_count": 0,  # TODO: Calculate from reviews table
            },
        }
