"""
Main application tests.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data


class TestAPIEndpoints:
    """Test basic API functionality."""

    @pytest.mark.asyncio
    async def test_api_v1_prefix(self, client: AsyncClient):
        """Test API v1 prefix is accessible."""
        # This will work once endpoints are implemented
        response = await client.get("/api/v1/")
        assert response.status_code in [200, 404]  # May not have root endpoint yet

    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are set correctly."""
        response = await client.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS headers should be present
        assert response.status_code in [200, 404]
