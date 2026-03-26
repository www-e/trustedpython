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
    pool_size=5,
    max_overflow=10,
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


@pytest.fixture(scope="session")
async def setup_database():
    """
    Set up database schema ONCE for all tests.
    Manually creates ENUMs and tables to avoid cache issues.
    """
    async with test_engine.begin() as conn:
        # Clean up any existing state including ENUMs with CASCADE
        for enum_name in ["deal_status", "game_type", "listing_status"]:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))

        await conn.execute(text("DROP TABLE IF EXISTS listing_mediators CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS deals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listing_images CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS exclusive_cards CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

        # Create ENUM types ONCE with values matching Python enums
        await conn.execute(text("CREATE TYPE game_type AS ENUM ('PUBG', 'FREE_FIRE', 'CALL_OF_DUTY', 'FORTNITE', 'MOBILE_LEGENDS', 'OTHER')"))
        await conn.execute(text("CREATE TYPE listing_status AS ENUM ('DRAFT', 'PENDING', 'ACTIVE', 'SOLD', 'PAUSED', 'ARCHIVED')"))
        await conn.execute(text("CREATE TYPE deal_status AS ENUM ('PENDING', 'IN_PROGRESS', 'AWAITING_PAYMENT', 'PAYMENT_VERIFIED', 'CREDENTIALS_EXCHANGED', 'COMPLETED', 'CANCELLED', 'DISPUTED')"))

        # Create tables manually using the exact SQL from models
        # Users table
        await conn.execute(text("""
            CREATE TABLE users (
                phone VARCHAR(20) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                is_active BOOLEAN NOT NULL,
                is_verified BOOLEAN NOT NULL,
                username VARCHAR(50),
                avatar_url VARCHAR(500),
                bio TEXT,
                rating NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
                total_deals_as_buyer INTEGER NOT NULL DEFAULT 0,
                total_deals_as_seller INTEGER NOT NULL DEFAULT 0,
                completed_deals INTEGER NOT NULL DEFAULT 0,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                UNIQUE (phone)
            )
        """))
        await conn.execute(text("CREATE INDEX ix_users_phone ON users (phone)"))

        # Categories table
        await conn.execute(text("""
            CREATE TABLE categories (
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                icon_url VARCHAR(500),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_popular BOOLEAN NOT NULL DEFAULT FALSE,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
            )
        """))
        await conn.execute(text("CREATE INDEX ix_categories_name ON categories (name)"))
        await conn.execute(text("CREATE INDEX ix_categories_is_popular ON categories (is_popular)"))

        # Listings table
        await conn.execute(text("""
            CREATE TABLE listings (
                seller_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                game_type game_type NOT NULL,
                level INTEGER,
                rank VARCHAR(100),
                server VARCHAR(100),
                skins_count INTEGER,
                characters_count INTEGER,
                price NUMERIC(10, 2) NOT NULL,
                status listing_status NOT NULL DEFAULT 'DRAFT',
                is_featured BOOLEAN NOT NULL DEFAULT FALSE,
                views_count INTEGER NOT NULL DEFAULT 0,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                FOREIGN KEY(seller_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
            )
        """))
        await conn.execute(text("CREATE INDEX ix_listings_seller_id ON listings (seller_id)"))
        await conn.execute(text("CREATE INDEX ix_listings_category_id ON listings (category_id)"))

        # Listing images table
        await conn.execute(text("""
            CREATE TABLE listing_images (
                listing_id INTEGER NOT NULL,
                image_url VARCHAR(500) NOT NULL,
                caption VARCHAR(200),
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_primary BOOLEAN NOT NULL DEFAULT FALSE,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX ix_listing_images_listing_id ON listing_images (listing_id)"))

        # Deals table
        await conn.execute(text("""
            CREATE TABLE deals (
                listing_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                mediator_id INTEGER,
                status deal_status NOT NULL DEFAULT 'PENDING',
                price NUMERIC(10, 2) NOT NULL,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                FOREIGN KEY(buyer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(seller_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(mediator_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """))
        await conn.execute(text("CREATE INDEX ix_deals_listing_id ON deals (listing_id)"))
        await conn.execute(text("CREATE INDEX ix_deals_buyer_id ON deals (buyer_id)"))
        await conn.execute(text("CREATE INDEX ix_deals_seller_id ON deals (seller_id)"))
        await conn.execute(text("CREATE INDEX ix_deals_status ON deals (status)"))

        # Listing mediators table
        await conn.execute(text("""
            CREATE TABLE listing_mediators (
                listing_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Exclusive cards table
        await conn.execute(text("""
            CREATE TABLE exclusive_cards (
                title VARCHAR(200) NOT NULL,
                tag VARCHAR(50) NOT NULL,
                button_text VARCHAR(100) NOT NULL,
                button_link VARCHAR(500) NOT NULL,
                background_type VARCHAR(20) NOT NULL,
                background_value VARCHAR(500) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                display_order INTEGER NOT NULL DEFAULT 0,
                display_until TIMESTAMP WITH TIME ZONE,
                id SERIAL NOT NULL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
            )
        """))
        await conn.execute(text("CREATE INDEX ix_exclusive_cards_is_active ON exclusive_cards (is_active)"))

    yield

    # Cleanup after ALL tests complete
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS listing_mediators CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS deals CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listing_images CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS exclusive_cards CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS deal_status CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS game_type CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS listing_status CASCADE"))


@pytest.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for each test.
    Uses SAVEPOINT transactions for isolation and automatic rollback.
    """
    async with TestAsyncSessionLocal() as session:
        # Start a transaction that we will rollback
        await session.begin()

        yield session

        # Explicitly rollback to undo any changes
        await session.rollback()


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
