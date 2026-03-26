"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db import get_db
from app.main import app


# Test database URL
TEST_DATABASE_URL = settings.database_url


# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "prepared_statement_cache_size": 0,  # Disable prepared statement caching
        "statement_cache_size": 0  # Disable statement caching
    }
)

# Create async session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for each test.
    Uses transactions for isolation and automatic rollback.
    """
    async with TestAsyncSessionLocal() as session:
        # Begin transaction for this test
        trans = await session.begin()

        yield session

        # Rollback the transaction to undo any changes
        await trans.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
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
    """Get test user data."""
    return {
        "phone": "+1234567890",
        "password": "SecurePass123!",
        "role": "buyer"
    }


@pytest.fixture
async def auth_headers() -> dict:
    """Get authentication headers for requests."""
    return {"Authorization": "Bearer test_token"}
