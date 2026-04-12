"""
Pytest Configuration and Fixtures

Provides shared fixtures and configuration for all tests across the application.
Uses SQLite in-memory database for fast, isolated testing without external dependencies.
"""

import asyncio
import pytest
from typing import AsyncGenerator, Generator, Dict, Any
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.main import app
from app.core.security import create_access_token, hash_password
from app.models.base import Base

# Test database URL using SQLite for fast in-memory testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """Provide mock user data."""
    return {
        "id": uuid4(),
        "username": "testuser",
        "email": "test@example.com",
        "phone": "+1234567890",
        "password_hash": hash_password("TestPass123!"),
        "is_email_verified": True,
        "is_active": True,
        "is_suspended": False,
    }


@pytest.fixture
def mock_user_register_data() -> Dict[str, str]:
    """Provide registration payload."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "phone": "+1234567891",
        "password": "SecurePass123!",
    }


@pytest.fixture
def mock_admin_data() -> Dict[str, Any]:
    """Provide mock admin user data."""
    return {
        "id": uuid4(),
        "username": "admin",
        "email": "admin@example.com",
        "phone": "+1234567892",
        "password_hash": hash_password("AdminPass123!"),
        "is_email_verified": True,
        "is_active": True,
        "is_suspended": False,
        "is_admin": True,
    }


@pytest.fixture
def auth_token(mock_user: Dict[str, Any]) -> str:
    """Generate a valid JWT token for testing."""
    return create_access_token(data={"sub": str(mock_user["id"]), "username": mock_user["username"]})


@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Provide authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def client(event_loop: asyncio.AbstractEventLoop) -> AsyncGenerator[AsyncClient, None]:
    """Create test client without database dependencies."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as ac:
        yield ac


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def patch_get_db(mock_db_session: AsyncMock):
    """Override get_db dependency with mock session."""
    from app.api.deps import get_db
    
    async def override():
        yield mock_db_session
    
    app.dependency_overrides[get_db] = override
    yield mock_db_session
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def patch_redis():
    """Override Redis dependency with mock."""
    from app.core import redis
    
    original_client = redis.redis_client
    redis.redis_client = AsyncMock()
    redis.redis_client.ping = AsyncMock(return_value=True)
    
    yield redis.redis_client
    
    redis.redis_client = original_client


@pytest.fixture
def patch_storage():
    """Mock storage service."""
    with patch("app.utils.storage.upload_file_to_storage") as mock_upload:
        mock_upload.return_value = "https://storage.example.com/test-file.jpg"
        yield mock_upload


@pytest.fixture
def sample_listing_data() -> Dict[str, Any]:
    """Provide sample listing data."""
    return {
        "title": "Epic Gaming Account",
        "price": 99.99,
        "game": "Fortnite",
        "description": "Level 500, rare skins",
        "is_premium": False,
    }


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Provide sample account data."""
    return {
        "title": "Pro Account",
        "price": 149.99,
        "game": "Valorant",
        "rank": "Immortal",
        "description": "High rank account",
    }


@pytest.fixture
def sample_deal_data() -> Dict[str, Any]:
    """Provide sample deal data."""
    return {
        "listing_id": str(uuid4()),
        "offer_price": 89.99,
        "message": "Interested in this account",
    }


@pytest.fixture
def sample_message_data() -> Dict[str, Any]:
    """Provide sample chat message data."""
    return {
        "content": "Hello, is this account still available?",
        "type": "text",
    }


@pytest.fixture
def sample_notification_data() -> Dict[str, Any]:
    """Provide sample notification data."""
    return {
        "title": "Test Notification",
        "message": "This is a test notification",
        "type": "info",
    }
