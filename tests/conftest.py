"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from app.core.config import settings
from app.db import get_db
from app.main import app
from app.models.base import Base


# Test database URL
TEST_DATABASE_URL = settings.database_url


# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
)

# Create async session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Yields:
        Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """
    Set up database schema once for all tests.
    """
    async with test_engine.begin() as conn:
        # Create ENUM types (ignore if already exists)
        try:
            await conn.execute(text("CREATE TYPE game_type AS ENUM ('PUBG', 'FREE_FIRE', 'CALL_OF_DUTY', 'FORTNITE', 'MOBILE_LEGENDS', 'OTHER')"))
        except Exception:
            pass  # Type already exists
        try:
            await conn.execute(text("CREATE TYPE listing_status AS ENUM ('draft', 'pending', 'active', 'sold', 'paused', 'archived')"))
        except Exception:
            pass  # Type already exists
        try:
            await conn.execute(text("CREATE TYPE deal_status AS ENUM ('pending', 'in_progress', 'awaiting_payment', 'payment_verified', 'credentials_exchanged', 'completed', 'cancelled', 'disputed')"))
        except Exception:
            pass  # Type already exists
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS deal_status CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS game_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS listing_status CASCADE"))


@pytest.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for tests with transaction isolation.

    Args:
        setup_database: Session-scoped fixture that sets up the schema

    Yields:
        Async database session
    """
    async with TestAsyncSessionLocal() as session:
        # Start transaction
        trans = await session.begin()
        try:
            yield session
        finally:
            # Always rollback to ensure clean state for next test
            await trans.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing.

    Args:
        db_session: Database session fixture

    Yields:
        Async HTTP client
    """
    async def override_get_db():
        """Override get_db dependency."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user_data() -> dict:
    """
    Get test user data.

    Returns:
        Test user data dictionary
    """
    return {
        "phone": "+1234567890",
        "password": "SecurePass123!",
        "role": "buyer"
    }


@pytest.fixture
async def auth_headers() -> dict:
    """
    Get authentication headers for requests.

    Returns:
        Headers with Bearer token
    """
    # TODO: Implement after auth is complete
    return {"Authorization": "Bearer test_token"}
