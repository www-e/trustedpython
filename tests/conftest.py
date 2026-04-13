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
async def authenticated_client(client: AsyncClient, auth_token: str) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
def account_id() -> str:
    """Provide a mock account ID."""
    return str(uuid4())


@pytest.fixture
def mediator_id() -> str:
    """Provide a mock mediator ID."""
    return str(uuid4())


@pytest.fixture
def deal_id() -> str:
    """Provide a mock deal ID."""
    return str(uuid4())


@pytest.fixture
def test_image() -> bytes:
    """Provide a minimal test image (1x1 JPEG)."""
    # Minimal valid JPEG file
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7tele),01H76tele\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd4\xff\xd9'


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
