"""Authentication tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+1234567890",
            "password": "SecurePass123!",
            "role": "buyer"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["phone"] == "+1234567890"
    assert data["role"] == "buyer"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "id" in data
    assert "password" not in data  # Password should not be in response


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient):
    """Test registration with duplicate phone number."""
    user_data = {
        "phone": "+1234567891",
        "password": "SecurePass123!",
        "role": "buyer"
    }

    # First registration should succeed
    response1 = await client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with same phone should fail
    response2 = await client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 409
    data = response2.json()
    assert "conflict" in data["error"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration with weak password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+1234567892",
            "password": "123",  # Too short
            "role": "buyer"
        }
    )

    # Should fail validation
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful login."""
    # Create user first
    user_service = UserService(db_session)
    user_data = UserCreate(
        phone="+1234567893",
        password="SecurePass123!",
        role=UserRole.BUYER
    )
    await user_service.register(user_data)

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+1234567893",
            "password": "SecurePass123!"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone"] == "+1234567893"
    assert len(data["access_token"]) > 20  # JWT should be reasonably long


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    """Test login with wrong password."""
    # Create user first
    user_service = UserService(db_session)
    user_data = UserCreate(
        phone="+1234567894",
        password="SecurePass123!",
        role=UserRole.BUYER
    )
    await user_service.register(user_data)

    # Login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+1234567894",
            "password": "WrongPassword!"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "authentication" in data["error"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+9999999999",
            "password": "DoesntMatter!"
        }
    )

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "not_found"


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, db_session: AsyncSession):
    """Test getting current authenticated user."""
    # Create and login user
    user_service = UserService(db_session)
    user_data = UserCreate(
        phone="+1234567895",
        password="SecurePass123!",
        role=UserRole.SELLER
    )
    await user_service.register(user_data)

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+1234567895",
            "password": "SecurePass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["phone"] == "+1234567895"
    assert data["role"] == "seller"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without authentication."""
    response = await client.get("/api/v1/auth/me")

    # Can be 401 (Unauthorized) or 403 (Forbidden) depending on how auth fails
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout endpoint."""
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert response.content == b""  # No content


@pytest.mark.asyncio
async def test_register_mediator_role(client: AsyncClient):
    """Test registering a user with mediator role."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+1234567896",
            "password": "SecurePass123!",
            "role": "mediator"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "mediator"
