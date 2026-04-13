"""
Test suite for Buy Flow endpoints.

Tests the complete buy flow including:
- Account browsing and details
- Mediator selection
- Deal creation and management
- Payment processing
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestBuyFlowAccounts:
    """Test account-related endpoints."""

    async def test_browse_accounts(self, client: AsyncClient):
        """Test browsing accounts with filters."""
        response = await client.get(
            "/api/v1/buy/accounts",
            params={
                "game": "Valorant",
                "price_min": 100,
                "price_max": 500,
                "sort": "price_asc",
                "page": 1,
                "limit": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accounts" in data["data"]
        assert "filters" in data["data"]
        assert "pagination" in data["data"]

    async def test_get_account_details(self, client: AsyncClient, account_id: str):
        """Test getting account details."""
        response = await client.get(f"/api/v1/buy/accounts/{account_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        account = data["data"]
        assert account["id"] == account_id
        assert "seller" in account
        assert "images" in account

    async def test_get_similar_accounts(self, client: AsyncClient, account_id: str):
        """Test getting similar accounts."""
        response = await client.get(
            f"/api/v1/buy/accounts/{account_id}/similar",
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accounts" in data["data"]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestBuyFlowMediators:
    """Test mediator-related endpoints."""

    async def test_list_mediators(self, client: AsyncClient):
        """Test listing mediators."""
        response = await client.get(
            "/api/v1/buy/mediators",
            params={
                "specialization": "Valorant",
                "sort": "rating",
                "page": 1,
                "limit": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "mediators" in data["data"]
        assert "pagination" in data["data"]

    async def test_get_mediator_details(self, client: AsyncClient, mediator_id: str):
        """Test getting mediator details."""
        response = await client.get(f"/api/v1/buy/mediators/{mediator_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mediator = data["data"]
        assert mediator["id"] == mediator_id
        assert "stats" in mediator

    async def test_get_mediator_reviews(self, client: AsyncClient, mediator_id: str):
        """Test getting mediator reviews."""
        response = await client.get(
            f"/api/v1/buy/mediators/{mediator_id}/reviews",
            params={"page": 1, "limit": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reviews" in data["data"]
        assert "average_rating" in data["data"]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestBuyFlowDeals:
    """Test deal-related endpoints."""

    async def test_create_deal(
        self,
        authenticated_client: AsyncClient,
        account_id: str,
        mediator_id: str
    ):
        """Test creating a deal."""
        response = await authenticated_client.post(
            "/api/v1/buy/deals",
            json={
                "account_id": account_id,
                "mediator_id": mediator_id,
                "quantity": 1,
                "notes": "Test deal"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        deal = data["data"]
        assert deal["status"] == "pending"
        assert "chat_room_id" in deal
        return deal["id"]

    async def test_get_deal_details(
        self,
        authenticated_client: AsyncClient,
        deal_id: str
    ):
        """Test getting deal details."""
        response = await authenticated_client.get(f"/api/v1/buy/deals/{deal_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        deal = data["data"]
        assert deal["id"] == deal_id
        assert "account" in deal
        assert "mediator" in deal
        assert "buyer" in deal
        assert "seller" in deal

    async def test_update_deal_status(
        self,
        authenticated_client: AsyncClient,
        deal_id: str
    ):
        """Test updating deal status."""
        response = await authenticated_client.put(
            f"/api/v1/buy/deals/{deal_id}/status",
            json={
                "status": "awaiting_payment",
                "notes": "Moving to payment stage"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "awaiting_payment"

    async def test_get_my_deals(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting user's deals."""
        response = await authenticated_client.get(
            "/api/v1/buy/deals/my",
            params={
                "role": "buyer",
                "status": "pending",
                "page": 1,
                "limit": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deals" in data["data"]
        assert "pagination" in data["data"]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestBuyFlowPayments:
    """Test payment-related endpoints."""

    async def test_submit_payment(
        self,
        authenticated_client: AsyncClient,
        deal_id: str,
        test_image: bytes
    ):
        """Test submitting payment."""
        response = await authenticated_client.post(
            f"/api/v1/buy/deals/{deal_id}/payment",
            data={"notes": "Payment proof"},
            files={"screenshot": ("screenshot.jpg", test_image, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "payment_submitted"
        assert "screenshot_url" in data["data"]

    async def test_confirm_payment(
        self,
        authenticated_client: AsyncClient,
        deal_id: str
    ):
        """Test confirming payment."""
        response = await authenticated_client.post(
            f"/api/v1/buy/deals/{deal_id}/payment/confirm",
            json={"notes": "Payment verified"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "verified"

    async def test_reject_payment(
        self,
        authenticated_client: AsyncClient,
        deal_id: str
    ):
        """Test rejecting payment."""
        response = await authenticated_client.post(
            f"/api/v1/buy/deals/{deal_id}/payment/reject",
            json={"reason": "Screenshot is unclear, please resubmit"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "rejected"
        assert "rejection_reason" in data["data"]

    async def test_check_payment_status(
        self,
        authenticated_client: AsyncClient,
        deal_id: str
    ):
        """Test checking payment status."""
        response = await authenticated_client.get(
            f"/api/v1/buy/deals/{deal_id}/payment/status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]


class TestBuyFlowErrors:
    """Test error handling."""

    async def test_create_deal_invalid_account(self, authenticated_client: AsyncClient):
        """Test creating deal with invalid account."""
        response = await authenticated_client.post(
            "/api/v1/buy/deals",
            json={
                "account_id": "00000000-0000-0000-0000-000000000000",
                "mediator_id": "00000000-0000-0000-0000-000000000000"
            }
        )
        assert response.status_code == 400

    async def test_unauthorized_deal_access(self, client: AsyncClient, deal_id: str):
        """Test accessing deal without authentication."""
        response = await client.get(f"/api/v1/buy/deals/{deal_id}")
        assert response.status_code == 401

    async def test_invalid_payment_file(self, authenticated_client: AsyncClient, deal_id: str):
        """Test uploading invalid file type."""
        response = await authenticated_client.post(
            f"/api/v1/buy/deals/{deal_id}/payment",
            files={"screenshot": ("test.txt", b"not an image", "text/plain")}
        )
        assert response.status_code == 400

    async def test_oversized_payment_file(self, authenticated_client: AsyncClient, deal_id: str):
        """Test uploading file larger than 5MB."""
        large_file = b"x" * (6 * 1024 * 1024)  # 6MB
        response = await authenticated_client.post(
            f"/api/v1/buy/deals/{deal_id}/payment",
            files={"screenshot": ("large.jpg", large_file, "image/jpeg")}
        )
        assert response.status_code == 400
