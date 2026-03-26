"""Fixtures for service layer tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.listing import Listing, Category
from app.models.enums import UserRole, ListingStatus, GameType
from app.services.user_auth import UserAuthService
from app.schemas.user import UserCreate
from app.repositories.user import UserRepository
from app.repositories.category import CategoryRepository
from app.repositories.listing import ListingRepository


@pytest.fixture
async def setup_user(db_session: AsyncSession):
    """Create a test user."""
    user_data = UserCreate(
        phone="+1234567890",
        password="password123",
        role=UserRole.BUYER
    )

    auth_service = UserAuthService(db_session)
    user = await auth_service.register(user_data)

    return user


@pytest.fixture
async def setup_admin(db_session: AsyncSession):
    """Create a test admin user."""
    user_data = UserCreate(
        phone="+1111111111",
        password="admin123",
        role=UserRole.ADMIN
    )

    auth_service = UserAuthService(db_session)
    user = await auth_service.register(user_data)

    return user


@pytest.fixture
async def setup_user_with_password(db_session: AsyncSession):
    """Create a test user and return user with password."""
    password = "testpassword123"
    user_data = UserCreate(
        phone="+1234567890",
        password=password,
        role=UserRole.BUYER
    )

    auth_service = UserAuthService(db_session)
    user = await auth_service.register(user_data)

    return user, password


@pytest.fixture
async def setup_category(db_session: AsyncSession):
    """Create a test category."""
    category_repo = CategoryRepository(db_session)
    category = await category_repo.create(
        name="Test Game",
        description="Test game category",
        is_active=True
    )

    return category


@pytest.fixture
async def setup_listing(db_session: AsyncSession, setup_category, setup_user):
    """Create a test listing."""
    category = setup_category
    seller = setup_user

    # Change seller role to SELLER
    from app.repositories.user import UserRepository
    user_repo = UserRepository(db_session)
    seller = await user_repo.update(seller.id, role=UserRole.SELLER)

    listing_repo = ListingRepository(db_session)
    listing = await listing_repo.create(
        seller_id=seller.id,
        category_id=category.id,
        title="Test Account",
        description="Test gaming account",
        game_type=GameType.PUBG,
        price=50.0,
        status=ListingStatus.DRAFT
    )

    return listing, seller


@pytest.fixture
async def setup_active_listing(db_session: AsyncSession, setup_category, setup_user):
    """Create an active test listing."""
    category = setup_category
    seller = setup_user

    # Change seller role to SELLER
    from app.repositories.user import UserRepository
    user_repo = UserRepository(db_session)
    seller = await user_repo.update(seller.id, role=UserRole.SELLER)

    listing_repo = ListingRepository(db_session)
    listing = await listing_repo.create(
        seller_id=seller.id,
        category_id=category.id,
        title="Active Account",
        description="Active gaming account",
        game_type=GameType.PUBG,
        price=100.0,
        status=ListingStatus.ACTIVE
    )

    return listing, seller
