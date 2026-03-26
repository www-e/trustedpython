"""Tests for UserProfileService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_profile import UserProfileService
from app.exceptions import NotFoundError, ConflictError


@pytest.mark.asyncio
async def test_get_profile_success(db_session: AsyncSession, setup_user):
    """Test successful profile retrieval."""
    user = setup_user

    service = UserProfileService(db_session)
    result = await service.get_profile(user.id)

    assert result.id == user.id
    assert result.phone == user.phone


@pytest.mark.asyncio
async def test_get_profile_not_found(db_session: AsyncSession):
    """Test profile retrieval with non-existent user."""
    service = UserProfileService(db_session)

    with pytest.raises(NotFoundError, match="not found"):
        await service.get_profile(99999)


@pytest.mark.asyncio
async def test_update_profile_success(db_session: AsyncSession, setup_user):
    """Test successful profile update."""
    user = setup_user

    service = UserProfileService(db_session)
    result = await service.update_profile(
        user.id,
        username="newusername",
        bio="New bio"
    )

    assert result.username == "newusername"
    assert result.bio == "New bio"


@pytest.mark.asyncio
async def test_update_profile_username_taken(db_session: AsyncSession, setup_user):
    """Test profile update with taken username."""
    user1 = setup_user

    # Create another user
    from app.services.user_auth import UserAuthService
    from app.schemas.user import UserCreate
    auth_service = UserAuthService(db_session)

    user2_data = UserCreate(
        phone="+9876543210",
        password="password123",
        role=user1.role
    )
    user2 = await auth_service.register(user2_data)
    user2.username = "takenusername"
    await db_session.commit()

    profile_service = UserProfileService(db_session)

    with pytest.raises(ConflictError, match="already taken"):
        await profile_service.update_profile(
            user1.id,
            username="takenusername"
        )


@pytest.mark.asyncio
async def test_deactivate_user_success(db_session: AsyncSession, setup_user):
    """Test successful user deactivation."""
    user = setup_user

    service = UserProfileService(db_session)
    result = await service.deactivate_user(user.id)

    assert result.is_active is False
