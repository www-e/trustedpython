"""
Tests for main app endpoints: root, health, docs.
"""

import pytest
from httpx import AsyncClient


class TestRootEndpoint:
    """Test root endpoint."""

    async def test_root_returns_200(self, client: AsyncClient):
        """Test root endpoint returns 200."""
        response = await client.get("/")
        assert response.status_code == 200

    async def test_root_returns_json(self, client: AsyncClient):
        """Test root endpoint returns JSON."""
        response = await client.get("/")
        assert response.headers["content-type"] == "application/json"

    async def test_root_contains_name(self, client: AsyncClient):
        """Test root response contains app name."""
        response = await client.get("/")
        data = response.json()
        assert "name" in data
        assert len(data["name"]) > 0

    async def test_root_contains_version(self, client: AsyncClient):
        """Test root response contains version."""
        response = await client.get("/")
        data = response.json()
        assert "version" in data

    async def test_root_contains_status(self, client: AsyncClient):
        """Test root response contains status."""
        response = await client.get("/")
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    async def test_root_contains_docs(self, client: AsyncClient):
        """Test root response contains docs URL."""
        response = await client.get("/")
        data = response.json()
        assert "docs" in data


class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_returns_200(self, client: AsyncClient):
        """Test health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_json(self, client: AsyncClient):
        """Test health endpoint returns JSON."""
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"

    async def test_health_contains_status(self, client: AsyncClient):
        """Test health response contains status."""
        response = await client.get("/health")
        data = response.json()
        assert "status" in data

    async def test_health_contains_database(self, client: AsyncClient):
        """Test health response contains database status."""
        response = await client.get("/health")
        data = response.json()
        assert "database" in data

    async def test_health_contains_redis(self, client: AsyncClient):
        """Test health response contains redis status."""
        response = await client.get("/health")
        data = response.json()
        assert "redis" in data

    async def test_health_status_values(self, client: AsyncClient):
        """Test health status has valid values."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["database"] in ["ok", "error"]
        assert data["redis"] in ["ok", "error"]


class TestDocsEndpoints:
    """Test documentation endpoints."""

    async def test_docs_accessible(self, client: AsyncClient):
        """Test docs endpoint is accessible."""
        response = await client.get("/docs")
        assert response.status_code in [200, 404]  # May be disabled in production

    async def test_openapi_json_accessible(self, client: AsyncClient):
        """Test OpenAPI schema is accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200

    async def test_openapi_schema_has_info(self, client: AsyncClient):
        """Test OpenAPI schema has info."""
        response = await client.get("/openapi.json")
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]

    async def test_openapi_schema_has_paths(self, client: AsyncClient):
        """Test OpenAPI schema has paths."""
        response = await client.get("/openapi.json")
        data = response.json()
        assert "paths" in data
        assert len(data["paths"]) > 0

    async def test_redoc_accessible(self, client: AsyncClient):
        """Test ReDoc endpoint is accessible."""
        response = await client.get("/redoc")
        assert response.status_code in [200, 404]  # May be disabled in production
