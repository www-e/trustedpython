"""Health check tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_api_docs(client: AsyncClient):
    """Test API documentation is accessible."""
    response = await client.get("/docs")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc(client: AsyncClient):
    """Test ReDoc documentation is accessible."""
    response = await client.get("/redoc")

    assert response.status_code == 200
