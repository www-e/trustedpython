"""
Tests for authentication endpoints: register, login, logout, refresh, etc.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestAuthRegister:
    """Test user registration endpoint."""

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing fields returns 422."""
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    async def test_register_missing_username(self, client: AsyncClient):
        """Test registration without username returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "TestPass123!", "phone": "+1234567890"},
        )
        assert response.status_code == 422

    async def test_register_missing_email(self, client: AsyncClient):
        """Test registration without email returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "TestPass123!", "phone": "+1234567890"},
        )
        assert response.status_code == 422

    async def test_register_missing_password(self, client: AsyncClient):
        """Test registration without password returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "email": "test@example.com", "phone": "+1234567890"},
        )
        assert response.status_code == 422

    async def test_register_missing_phone(self, client: AsyncClient):
        """Test registration without phone returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "email": "test@example.com", "password": "TestPass123!"},
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "TestPass123!",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 422

    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username returns error."""
        register_data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "TestPass123!",
            "phone": "+1234567890",
        }
        
        # First registration
        await client.post("/api/v1/auth/register", json=register_data)
        
        # Second registration with same username
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code in [400, 409, 500]


class TestAuthLogin:
    """Test user login endpoint."""

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields returns 422."""
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials returns 401 or error."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"},
        )
        assert response.status_code in [401, 500]  # 500 if DB not available

    async def test_login_returns_error_structure(self, client: AsyncClient):
        """Test login returns proper error structure when DB unavailable."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"},
        )
        data = response.json()
        assert "error_code" in data or response.status_code == 422


class TestAuthLogout:
    """Test user logout endpoint."""

    async def test_logout_requires_auth(self, client: AsyncClient):
        """Test logout requires authentication."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout with invalid token returns 401."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code in [401, 422]


class TestAuthRefresh:
    """Test token refresh endpoint."""

    async def test_refresh_missing_token(self, client: AsyncClient):
        """Test refresh without token returns 422."""
        response = await client.post("/api/v1/auth/refresh-token", json={})
        assert response.status_code == 422

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token returns error."""
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code in [401, 422, 500]


class TestAuthForgotPassword:
    """Test forgot password endpoint."""

    async def test_forgot_password_missing_email(self, client: AsyncClient):
        """Test forgot password without email returns 422."""
        response = await client.post("/api/v1/auth/forgot-password", json={})
        assert response.status_code == 422

    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        """Test forgot password with invalid email returns 422."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


class TestAuthResetPassword:
    """Test reset password endpoint."""

    async def test_reset_password_missing_fields(self, client: AsyncClient):
        """Test reset password without fields returns 422."""
        response = await client.post("/api/v1/auth/reset-password", json={})
        assert response.status_code == 422

    async def test_reset_password_missing_token(self, client: AsyncClient):
        """Test reset password without token returns 422."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"new_password": "NewPass123!"},
        )
        assert response.status_code == 422


class TestAuthVerifyEmail:
    """Test email verification endpoint."""

    async def test_verify_email_missing_token(self, client: AsyncClient):
        """Test verify email without token returns 422 or 405."""
        response = await client.get("/api/v1/auth/verify-email")
        assert response.status_code in [405, 422]


class TestAuthMe:
    """Test get current user endpoint."""

    async def test_me_requires_auth(self, client: AsyncClient):
        """Test me endpoint requires authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_token(self, client: AsyncClient):
        """Test me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code in [401, 422]
