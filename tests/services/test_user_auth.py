"""Tests for UserAuthService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_auth import UserAuthService
from app.schemas.user import UserCreate
from app.models.enums import UserRole
from app.exceptions import ConflictError, AuthenticationError, NotFoundError


@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession):
    """Test successful user registration."""
    user_data = UserCreate(
        phone="+1234567890",
        password="SecurePass123",
        role=UserRole.BUYER
    )

    service = UserAuthService(db_session)
    user = await service.register(user_data)

    assert user.phone == "+1234567890"
    assert user.role == UserRole.BUYER
    assert user.is_active is True


@pytest.mark.asyncio
async def test_register_duplicate_phone(db_session: AsyncSession, setup_user):
    """Test registration with duplicate phone."""
    existing_user = setup_user

    user_data = UserCreate(
        phone=existing_user.phone,
        password="SecurePass123",
        role=UserRole.BUYER
    )

    service = UserAuthService(db_session)

    with pytest.raises(ConflictError, match="already exists"):
        await service.register(user_data)


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, setup_user_with_password):
    """Test successful login."""
    user, password = setup_user_with_password

    service = UserAuthService(db_session)
    result = await service.login(user.phone, password)

    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert result["user"].id == user.id


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession, setup_user):
    """Test login with wrong password."""
    user = setup_user

    service = UserAuthService(db_session)

    with pytest.raises(AuthenticationError, match="Invalid password"):
        await service.login(user.phone, "wrongpassword")


@pytest.mark.asyncio
async def test_login_user_not_found(db_session: AsyncSession):
    """Test login with non-existent user."""
    service = UserAuthService(db_session)

    with pytest.raises(NotFoundError, match="not found"):
        await service.login("+9999999999", "password")


@pytest.mark.asyncio
async def test_login_inactive_user(db_session: AsyncSession, setup_user):
    """Test login with inactive user."""
    user = setup_user

    # Deactivate user
    user.is_active = False

    service = UserAuthService(db_session)

    with pytest.raises(AuthenticationError, match="inactive"):
        await service.login(user.phone, "password123")
