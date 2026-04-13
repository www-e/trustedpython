"""
Test Sell Flow API endpoints.

Tests the complete sell flow including listing creation, preview,
image upload, categories, games, publishing, and analytics.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestSellRoutes:
    """Test sell flow endpoints."""

    @pytest.mark.asyncio
    async def test_create_listing_success(self, client: TestClient, auth_headers: dict):
        """Test successful listing creation."""
        # First upload an image
        response = client.post(
            "/api/v1/sell/upload-image",
            headers=auth_headers,
            files={"images": ("test.jpg", b"fake_image_data", "image/jpeg")}
        )
        assert response.status_code == 201
        image_data = response.json()
        image_id = image_data["data"]["images"][0]["id"]

        # Create listing
        listing_data = {
            "title": "Max Level Account",
            "price": 450.00,
            "game": "Fortnite",
            "category_id": str(uuid4()),  # Will need valid category
            "description": "Fully maxed account with rare skins",
            "image_ids": [image_id],
            "is_premium": False,
            "tier": "Regular"
        }

        response = client.post(
            "/api/v1/sell/listings",
            headers=auth_headers,
            json=listing_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Max Level Account"
        assert data["data"]["price"] == 450.00
        assert data["data"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_listing_no_images(self, client: TestClient, auth_headers: dict):
        """Test listing creation fails without images."""
        listing_data = {
            "title": "Max Level Account",
            "price": 450.00,
            "game": "Fortnite",
            "category_id": str(uuid4()),
            "description": "Fully maxed account",
            "image_ids": [],
            "is_premium": False
        }

        response = client.post(
            "/api/v1/sell/listings",
            headers=auth_headers,
            json=listing_data
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_preview_listing(self, client: TestClient, auth_headers: dict):
        """Test listing preview."""
        preview_data = {
            "title": "Test Account",
            "price": 299.99,
            "game": "Valorant",
            "description": "Test description",
            "image_urls": ["https://example.com/image.jpg"],
            "is_premium": True,
            "tier": "Gold"
        }

        response = client.post(
            "/api/v1/sell/listings/preview",
            headers=auth_headers,
            json=preview_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["preview"]["title"] == "Test Account"
        assert data["data"]["preview"]["formatted_price"] == "$299.99"
        assert data["data"]["preview"]["estimated_views"] is not None

    @pytest.mark.asyncio
    async def test_get_categories(self, client: TestClient):
        """Test getting categories list."""
        response = client.get("/api/v1/sell/categories")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "categories" in data["data"]
        assert isinstance(data["data"]["categories"], list)

    @pytest.mark.asyncio
    async def test_get_games(self, client: TestClient):
        """Test getting games list."""
        response = client.get("/api/v1/sell/games")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "games" in data["data"]
        assert isinstance(data["data"]["games"], list)

    @pytest.mark.asyncio
    async def test_upload_images(self, client: TestClient, auth_headers: dict):
        """Test image upload."""
        # This will need actual image files in real tests
        response = client.post(
            "/api/v1/sell/upload-image",
            headers=auth_headers,
            files={"images": ("test.jpg", b"fake_image_data", "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "images" in data["data"]

    @pytest.mark.asyncio
    async def test_upload_images_too_many(self, client: TestClient, auth_headers: dict):
        """Test image upload with too many files."""
        files = [
            ("images", (f"test{i}.jpg", b"fake_data", "image/jpeg"))
            for i in range(11)
        ]

        response = client.post(
            "/api/v1/sell/upload-image",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_listing(self, client: TestClient, auth_headers: dict, test_listing_id: uuid4):
        """Test updating a listing."""
        update_data = {
            "title": "Updated Title",
            "price": 399.99
        }

        response = client.put(
            f"/api/v1/sell/listings/{test_listing_id}",
            headers=auth_headers,
            json=update_data
        )

        # Will need actual listing ID in real test
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_publish_listing(self, client: TestClient, auth_headers: dict, test_listing_id: uuid4):
        """Test publishing a listing."""
        response = client.post(
            f"/api/v1/sell/listings/{test_listing_id}/publish",
            headers=auth_headers
        )

        # Will need actual listing ID in real test
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_unpublish_listing(self, client: TestClient, auth_headers: dict, test_listing_id: uuid4):
        """Test unpublishing a listing."""
        response = client.post(
            f"/api/v1/sell/listings/{test_listing_id}/unpublish",
            headers=auth_headers
        )

        # Will need actual listing ID in real test
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_analytics(self, client: TestClient, auth_headers: dict):
        """Test getting seller analytics."""
        response = client.get(
            "/api/v1/sell/analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analytics" in data["data"]
        analytics = data["data"]["analytics"]
        assert "total_listings" in analytics
        assert "active_listings" in analytics
        assert "sold_listings" in analytics
        assert "total_views" in analytics
        assert "total_revenue" in analytics
