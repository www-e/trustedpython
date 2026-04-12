"""
Tests for Pydantic schemas: user, auth, listing, deal, chat, notification, etc.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.user import UserResponse, UserCreate, LoginRequest
from app.schemas.common import APIResponse, ErrorResponse, PaginationSchema
from app.schemas.listing import ListingResponse, CreateListingRequest
from app.schemas.deal import DealResponse, CreateDealRequest
from app.schemas.chat import ChatRoomResponse, MessageResponse, SendMessageRequest
from app.schemas.notification import NotificationResponse, CreateNotificationRequest
from app.schemas.security import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    SecurityScoreResponse,
    TwoFactorSetupResponse,
    SuccessResponse,
)
from app.schemas.home import HomeFeedResponse, FeaturedAccountsResponse
from app.schemas.admin import AdminUserResponse, AdminListingResponse


class TestUserSchemas:
    """Test user-related schemas."""

    def test_user_create_valid(self):
        """Test valid user creation."""
        data = UserCreate(
            username="testuser",
            email="test@example.com",
            phone="+1234567890",
            password="TestPass123!",
        )
        assert data.username == "testuser"
        assert data.email == "test@example.com"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                phone="+1234567890",
                password="TestPass123!",
            )

    def test_user_create_weak_password(self):
        """Test user creation with weak password."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                phone="+1234567890",
                password="123",
            )

    def test_user_login_valid(self):
        """Test valid user login."""
        data = LoginRequest(username="testuser", password="TestPass123!")
        assert data.username == "testuser"

    def test_user_response(self):
        """Test user response schema."""
        user_id = uuid4()
        response = UserResponse(
            id=user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
        )
        assert response.username == "testuser"
        assert response.is_active is True


class TestCommonSchemas:
    """Test common schemas."""

    def test_api_response_success(self):
        """Test APIResponse success creation."""
        response = APIResponse.success_response(
            data={"key": "value"},
            message="Success",
        )
        assert response.data == {"key": "value"}
        assert response.message == "Success"

    def test_api_response_create(self):
        """Test APIResponse create method."""
        response = APIResponse.create(
            data={"key": "value"},
            message="Success",
        )
        assert response.data == {"key": "value"}

    def test_error_response(self):
        """Test ErrorResponse creation."""
        error = ErrorResponse.create(
            error_code="TEST_ERROR",
            message="Test error message",
            details={"field": ["is required"]},
        )
        assert error.error_code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details == {"field": ["is required"]}

    def test_pagination_schema(self):
        """Test PaginationSchema creation."""
        pagination = PaginationSchema.create(
            page=1,
            limit=20,
            total=100,
        )
        assert pagination.page == 1
        assert pagination.limit == 20
        assert pagination.total == 100
        assert pagination.pages == 5
        assert pagination.has_next is True

    def test_pagination_schema_no_next(self):
        """Test PaginationSchema with no next page."""
        pagination = PaginationSchema.create(
            page=5,
            limit=20,
            total=100,
        )
        assert pagination.has_next is False


class TestListingSchemas:
    """Test listing-related schemas."""

    def test_create_listing_request_valid(self):
        """Test valid listing creation."""
        data = CreateListingRequest(
            title="Epic Gaming Account",
            price=99.99,
            game="Fortnite",
            description="Level 500",
        )
        assert data.title == "Epic Gaming Account"
        assert data.price == 99.99

    def test_create_listing_request_missing_title(self):
        """Test listing creation without title."""
        with pytest.raises(ValidationError):
            CreateListingRequest(
                price=99.99,
                game="Fortnite",
            )

    def test_listing_response(self):
        """Test listing response schema."""
        listing_id = uuid4()
        response = ListingResponse(
            id=listing_id,
            title="Epic Gaming Account",
            price=99.99,
            game="Fortnite",
            is_published=True,
        )
        assert response.title == "Epic Gaming Account"
        assert response.is_published is True


class TestDealSchemas:
    """Test deal-related schemas."""

    def test_create_deal_request(self):
        """Test creating a deal request."""
        listing_id = uuid4()
        data = CreateDealRequest(
            listing_id=listing_id,
            offer_price=89.99,
            message="Interested",
        )
        assert data.offer_price == 89.99

    def test_deal_response(self):
        """Test deal response schema."""
        deal_id = uuid4()
        response = DealResponse(
            id=deal_id,
            status="pending",
            total_amount=99.99,
            currency="EGP",
        )
        assert response.status == "pending"


class TestChatSchemas:
    """Test chat-related schemas."""

    def test_send_message_request(self):
        """Test sending a message."""
        data = SendMessageRequest(
            content="Hello!",
            type="text",
        )
        assert data.content == "Hello!"

    def test_message_response(self):
        """Test message response schema."""
        message_id = uuid4()
        sender_id = uuid4()
        response = MessageResponse(
            id=message_id,
            sender_id=sender_id,
            sender_name="TestUser",
            content="Hello!",
            type="text",
            timestamp=datetime.now(),
            is_read=False,
            attachments=[],
        )
        assert response.content == "Hello!"

    def test_chat_room_response(self):
        """Test chat room response schema."""
        room_id = uuid4()
        response = ChatRoomResponse(
            id=room_id,
            name="Test Room",
            type="private",
            participants=[],
            unread_count=0,
            is_active=True,
            created_at=datetime.now(),
        )
        assert response.type == "private"


class TestNotificationSchemas:
    """Test notification-related schemas."""

    def test_create_notification_request(self):
        """Test creating notification request."""
        data = CreateNotificationRequest(
            title="Test",
            message="Test message",
            type="info",
        )
        assert data.title == "Test"

    def test_notification_response(self):
        """Test notification response schema."""
        notif_id = uuid4()
        response = NotificationResponse(
            id=notif_id,
            title="Test",
            message="Test message",
            type="info",
            is_read=False,
            created_at=datetime.now(),
        )
        assert response.type == "info"


class TestSecuritySchemas:
    """Test security-related schemas."""

    def test_change_password_request(self):
        """Test change password request."""
        data = ChangePasswordRequest(
            current_password="OldPass123!",
            new_password="NewPass123!",
        )
        assert data.current_password == "OldPass123!"

    def test_change_password_response(self):
        """Test change password response."""
        response = ChangePasswordResponse(success=True, message="Password changed")
        assert response.success is True

    def test_security_score_response(self):
        """Test security score response."""
        response = SecurityScoreResponse(
            score=85,
            level="good",
            vulnerabilities=[],
        )
        assert response.score == 85

    def test_enable_2fa_response(self):
        """Test enable 2FA response."""
        response = TwoFactorSetupResponse(
            secret="ABC123",
            qr_code_url="otpauth://...",
            backup_codes=["code1", "code2"],
        )
        assert response.secret == "ABC123"


class TestHomeSchemas:
    """Test home-related schemas."""

    def test_home_feed_response(self):
        """Test home feed response schema."""
        response = HomeFeedResponse(
            items=[],
            total=0,
        )
        assert response.total == 0

    def test_featured_accounts_response(self):
        """Test featured accounts response."""
        response = FeaturedAccountsResponse(
            accounts=[],
        )
        assert response.accounts == []


class TestAdminSchemas:
    """Test admin-related schemas."""

    def test_admin_user_response(self):
        """Test admin user response."""
        user_id = uuid4()
        response = AdminUserResponse(
            id=user_id,
            username="admin",
            email="admin@example.com",
            is_active=True,
            is_suspended=False,
        )
        assert response.username == "admin"

    def test_admin_listing_response(self):
        """Test admin listing response."""
        listing_id = uuid4()
        response = AdminListingResponse(
            id=listing_id,
            title="Test Listing",
            status="pending",
        )
        assert response.status == "pending"
