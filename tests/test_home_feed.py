"""Test suite for Home Feed API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestHomeFeedEndpoints:
    """Test home feed API endpoints."""

    @pytest.mark.asyncio
    async def test_get_home_feed_success(self, client: AsyncClient):
        """Test successful home feed retrieval."""
        response = await client.get("/api/v1/home/feed")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "featured_accounts" in data["data"]
        assert "accounts" in data["data"]
        assert "categories" in data["data"]
        assert "pagination" in data["data"]

    @pytest.mark.asyncio
    async def test_get_home_feed_with_filters(self, client: AsyncClient):
        """Test home feed with category and game filters."""
        response = await client.get(
            "/api/v1/home/feed",
            params={"category": "action", "game": "PUBG", "page": 1, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "pagination" in data["data"]
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_featured_accounts_success(self, client: AsyncClient):
        """Test successful featured accounts retrieval."""
        response = await client.get("/api/v1/home/featured")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "accounts" in data["data"]
        assert isinstance(data["data"]["accounts"], list)

    @pytest.mark.asyncio
    async def test_get_featured_accounts_with_limit(self, client: AsyncClient):
        """Test featured accounts with custom limit."""
        response = await client.get("/api/v1/home/featured?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]["accounts"]) <= 5

    @pytest.mark.asyncio
    async def test_get_featured_accounts_invalid_limit(self, client: AsyncClient):
        """Test featured accounts with invalid limit (should fail validation)."""
        response = await client.get("/api/v1/home/featured?limit=25")

        # Should fail validation or auto-cap to 20
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_get_categories_success(self, client: AsyncClient):
        """Test successful categories retrieval."""
        response = await client.get("/api/v1/home/categories")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "categories" in data["data"]
        assert isinstance(data["data"]["categories"], list)

    @pytest.mark.asyncio
    async def test_get_promo_banners_success(self, client: AsyncClient):
        """Test successful promo banners retrieval."""
        response = await client.get("/api/v1/home/promo")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "banners" in data["data"]
        assert isinstance(data["data"]["banners"], list)

    @pytest.mark.asyncio
    async def test_get_faq_success(self, client: AsyncClient):
        """Test successful FAQ retrieval."""
        response = await client.get("/api/v1/home/faq")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "faq_items" in data["data"]
        assert isinstance(data["data"]["faq_items"], list)

    @pytest.mark.asyncio
    async def test_search_accounts_success(self, client: AsyncClient):
        """Test successful account search."""
        response = await client.get(
            "/api/v1/home/search",
            params={"q": "PUBG"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "query" in data["data"]
        assert "total_results" in data["data"]
        assert "accounts" in data["data"]
        assert "filters" in data["data"]
        assert "pagination" in data["data"]

    @pytest.mark.asyncio
    async def test_search_accounts_with_filters(self, client: AsyncClient):
        """Test account search with filters."""
        response = await client.get(
            "/api/v1/home/search",
            params={
                "q": "account",
                "game": "PUBG",
                "price_min": 100,
                "price_max": 1000,
                "sort": "price_asc",
                "page": 1,
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["query"] == "account"

    @pytest.mark.asyncio
    async def test_search_accounts_invalid_query(self, client: AsyncClient):
        """Test search with invalid query (too short)."""
        response = await client.get(
            "/api/v1/home/search",
            params={"q": "a"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_games_success(self, client: AsyncClient):
        """Test successful games retrieval."""
        response = await client.get("/api/v1/home/games")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "games" in data["data"]
        assert isinstance(data["data"]["games"], list)

    @pytest.mark.asyncio
    async def test_get_games_with_sort(self, client: AsyncClient):
        """Test games retrieval with custom sort."""
        response = await client.get(
            "/api/v1/home/games",
            params={"sort": "popularity", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]["games"]) <= 10

    @pytest.mark.asyncio
    async def test_get_game_accounts_success(self, client: AsyncClient, game_id: uuid4):
        """Test successful game accounts retrieval."""
        response = await client.get(f"/api/v1/home/games/{game_id}/accounts")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "game" in data["data"]
        assert "accounts" in data["data"]
        assert "pagination" in data["data"]

    @pytest.mark.asyncio
    async def test_get_game_accounts_not_found(self, client: AsyncClient):
        """Test game accounts retrieval with non-existent game."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/home/games/{fake_id}/accounts")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rate_limiting_search(self, client: AsyncClient):
        """Test rate limiting on search endpoint."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(35):  # Exceed the 30/minute limit
            response = await client.get(
                "/api/v1/home/search",
                params={"q": f"test{i}"}
            )
            responses.append(response)

        # Some requests should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Expected rate limiting to kick in after 30 requests"


# Pytest fixtures for testing
@pytest.fixture
async def client(async_client):
    """Get test client."""
    return async_client


@pytest.fixture
def game_id():
    """Get a test game ID."""
    return uuid4()
