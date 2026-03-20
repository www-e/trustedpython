"""Category tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate
from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_create_category_as_admin(client: AsyncClient, db_session: AsyncSession):
    """Test category creation by admin."""
    # Create admin user
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate
    user_service = UserService(db_session)
    admin_data = UserCreate(
        phone="+1234567890",
        password="AdminPass123!",
        role=UserRole.ADMIN
    )
    admin = await user_service.register(admin_data)

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+1234567890",
            "password": "AdminPass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Create category
    response = await client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "PUBG",
            "description": "PlayerUnknown's Battlegrounds",
            "is_active": True,
            "sort_order": 1
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "PUBG"
    assert data["description"] == "PlayerUnknown's Battlegrounds"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_category_as_seller_forbidden(client: AsyncClient, db_session: AsyncSession):
    """Test that sellers cannot create categories."""
    # Create seller user
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate
    user_service = UserService(db_session)
    seller_data = UserCreate(
        phone="+1234567891",
        password="SellerPass123!",
        role=UserRole.SELLER
    )
    await user_service.register(seller_data)

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+1234567891",
            "password": "SellerPass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Try to create category (should fail)
    response = await client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Game",
            "description": "Test"
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient, db_session: AsyncSession):
    """Test getting all categories."""
    # Create test categories
    service = CategoryService(db_session)
    await service.create_category(CategoryCreate(name="PUBG", description="PUBG Game"))
    await service.create_category(CategoryCreate(name="Free Fire", description="Free Fire Game"))

    # Get categories
    response = await client.get("/api/v1/categories")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(c["name"] == "PUBG" for c in data)
    assert any(c["name"] == "Free Fire" for c in data)


@pytest.mark.asyncio
async def test_get_category_by_id(client: AsyncClient, db_session: AsyncSession):
    """Test getting a category by ID."""
    service = CategoryService(db_session)
    category = await service.create_category(CategoryCreate(name="PUBG", description="PUBG"))

    # Get category
    response = await client.get(f"/api/v1/categories/{category.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PUBG"
    assert data["id"] == category.id


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, db_session: AsyncSession):
    """Test updating a category."""
    # Create admin user and category
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate
    user_service = UserService(db_session)
    admin = await user_service.register(UserCreate(
        phone="+1234567892",
        password="AdminPass123!",
        role=UserRole.ADMIN
    ))

    category_service = CategoryService(db_session)
    category = await category_service.create_category(CategoryCreate(name="Old Name"))

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567892", "password": "AdminPass123!"}
    )
    token = login_response.json()["access_token"]

    # Update category
    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name", "description": "Updated description"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_search_categories(client: AsyncClient, db_session: AsyncSession):
    """Test searching categories."""
    service = CategoryService(db_session)
    await service.create_category(CategoryCreate(name="PUBG", description="PUBG Game"))
    await service.create_category(CategoryCreate(name="Free Fire", description="Free Fire Game"))
    await service.create_category(CategoryCreate(name="Call of Duty", description="COD Game"))

    # Search for "fire"
    response = await client.get("/api/v1/categories/search?q=fire")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Free Fire"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, db_session: AsyncSession):
    """Test deleting a category."""
    # Create admin
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate
    user_service = UserService(db_session)
    admin = await user_service.register(UserCreate(
        phone="+1234567893",
        password="AdminPass123!",
        role=UserRole.ADMIN
    ))

    category_service = CategoryService(db_session)
    category = await category_service.create_category(CategoryCreate(name="To Delete"))

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567893", "password": "AdminPass123!"}
    )
    token = login_response.json()["access_token"]

    # Delete category
    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204
