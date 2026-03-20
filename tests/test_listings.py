"""Listing tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.listing_service import ListingService
from app.services.category_service import CategoryService
from app.services.user_service import UserService
from app.schemas.listing import ListingCreate, ListingUpdate
from app.schemas.category import CategoryCreate
from app.schemas.user import UserCreate
from app.models.enums import UserRole, GameType, ListingStatus


@pytest.fixture
async def test_seller(db_session: AsyncSession):
    """Create a test seller user."""
    user_service = UserService(db_session)
    seller = await user_service.register(UserCreate(
        phone="+1234567890",
        password="SellerPass123!",
        role=UserRole.SELLER
    ))
    return seller


@pytest.fixture
async def test_category(db_session: AsyncSession):
    """Create a test category."""
    category_service = CategoryService(db_session)
    category = await category_service.create_category(CategoryCreate(
        name="PUBG",
        description="PlayerUnknown's Battlegrounds"
    ))
    return category


@pytest.mark.asyncio
async def test_create_listing(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test listing creation by seller."""
    # Login as seller
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567890", "password": "SellerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Create listing
    response = await client.post(
        "/api/v1/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Level 100 PUBG Account",
            "description": "Max level account with rare skins",
            "category_id": test_category.id,
            "game_type": "pubg",
            "level": 100,
            "rank": "Conqueror",
            "server": "NA",
            "skins_count": 50,
            "characters_count": 10,
            "price": 299.99,
            "is_featured": False
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Level 100 PUBG Account"
    assert data["price"] == 299.99
    assert data["status"] == "draft"
    assert data["seller_id"] == test_seller.id


@pytest.mark.asyncio
async def test_create_listing_as_buyer_forbidden(client: AsyncClient, db_session: AsyncSession, test_category):
    """Test that buyers cannot create listings."""
    # Create buyer
    user_service = UserService(db_session)
    await user_service.register(UserCreate(
        phone="+1234567891",
        password="BuyerPass123!",
        role=UserRole.BUYER
    ))

    # Login as buyer
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567891", "password": "BuyerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Try to create listing
    response = await client.post(
        "/api/v1/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Listing",
            "description": "Test",
            "category_id": test_category.id,
            "game_type": "pubg",
            "price": 100.0
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_listings(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test getting all listings."""
    # Create some listings
    listing_service = ListingService(db_session)
    await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Listing 1",
        description="Test 1",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=100.0
    ))
    await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Listing 2",
        description="Test 2",
        category_id=test_category.id,
        game_type=GameType.FREE_FIRE,
        price=150.0
    ))

    # Get all listings (will return empty since they're drafts)
    response = await client.get("/api/v1/listings")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_listing_by_id(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test getting a specific listing."""
    listing_service = ListingService(db_session)
    listing = await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Test Listing",
        description="Test Description",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=99.99
    ))

    # Get listing
    response = await client.get(f"/api/v1/listings/{listing.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Listing"
    assert data["price"] == 99.99
    assert "images" in data


@pytest.mark.asyncio
async def test_update_listing(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test updating a listing."""
    # Create listing
    listing_service = ListingService(db_session)
    listing = await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Original Title",
        description="Original Description",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=100.0
    ))

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567890", "password": "SellerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Update listing
    response = await client.patch(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Title",
            "price": 149.99
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["price"] == 149.99


@pytest.mark.asyncio
async def test_publish_listing(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test publishing a draft listing."""
    # Create draft listing
    listing_service = ListingService(db_session)
    listing = await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Draft Listing",
        description="Draft",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=100.0
    ))

    assert listing.status == ListingStatus.DRAFT

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567890", "password": "SellerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Publish listing
    response = await client.post(
        f"/api/v1/listings/{listing.id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_search_listings(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test searching listings."""
    listing_service = ListingService(db_session)

    # Create listings
    pubg_listing = await listing_service.create_listing(test_seller.id, ListingCreate(
        title="PUBG Account with Skins",
        description="Lots of rare skins",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=200.0
    ))
    await listing_service.create_listing(test_seller.id, ListingCreate(
        title="Free Fire Account",
        description="Max level account",
        category_id=test_category.id,
        game_type=GameType.FREE_FIRE,
        price=50.0
    ))

    # Publish the PUBG listing so it can be found in search
    await listing_service.publish_listing(pubg_listing.id, test_seller.id)

    # Search for "PUBG"
    response = await client.get("/api/v1/listings/search?q=PUBG")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("PUBG" in l["title"] for l in data)


@pytest.mark.asyncio
async def test_get_my_listings(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test getting current user's listings."""
    # Create listings
    listing_service = ListingService(db_session)
    await listing_service.create_listing(test_seller.id, ListingCreate(
        title="My Listing 1",
        description="Test",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=100.0
    ))
    await listing_service.create_listing(test_seller.id, ListingCreate(
        title="My Listing 2",
        description="Test",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=150.0
    ))

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567890", "password": "SellerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Get my listings
    response = await client.get(
        "/api/v1/listings/my",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_listing(client: AsyncClient, db_session: AsyncSession, test_seller, test_category):
    """Test deleting a listing."""
    # Create listing
    listing_service = ListingService(db_session)
    listing = await listing_service.create_listing(test_seller.id, ListingCreate(
        title="To Delete",
        description="Will be deleted",
        category_id=test_category.id,
        game_type=GameType.PUBG,
        price=100.0
    ))

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+1234567890", "password": "SellerPass123!"}
    )
    token = login_response.json()["access_token"]

    # Delete listing
    response = await client.delete(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204
