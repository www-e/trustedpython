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
from app.schemas.deal import (
    DealResponse, CreateDealRequest, DealStatus, PaymentStatus,
    AccountSummarySchema, MediatorSummarySchema, UserSummarySchema, PaymentInfoSchema
)
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
from app.schemas.admin import UserDetailResponse, ListingModerationResponse


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
        # UserResponse has required fields including id (int), created_at
        response = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        assert response.username == "testuser"
        assert response.is_verified is True


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
        response = APIResponse.success_response(
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
        assert pagination.total_pages == 5
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
        # CreateListingRequest requires category_id and at least 1 image
        from uuid import uuid4
        data = CreateListingRequest(
            title="Epic Gaming Account",
            price=99.99,
            game="Fortnite",
            category_id=uuid4(),
            description="Level 500",
            image_ids=[uuid4()],
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
            status="active",
            is_premium=False,
            created_at=datetime.utcnow(),
        )
        assert response.title == "Epic Gaming Account"
        assert response.status == "active"


class TestDealSchemas:
    """Test deal-related schemas."""

    def test_create_deal_request(self):
        """Test creating a deal request."""
        # CreateDealRequest uses account_id and mediator_id (not listing_id and offer_price)
        data = CreateDealRequest(
            account_id=str(uuid4()),
            mediator_id=str(uuid4()),
            notes="Interested",
        )
        assert data.notes == "Interested"

    def test_deal_response(self):
        """Test deal response schema."""
        deal_id = str(uuid4())
        # DealResponse requires buyer_id, seller_id, chat_room_id
        response = DealResponse(
            id=deal_id,
            status=DealStatus.PENDING,
            total_amount=99.99,
            currency="EGP",
            account=AccountSummarySchema(id="1", title="Test Account", price=99.99, game="Fortnite"),
            mediator=MediatorSummarySchema(id="1", name="Mediator", avatar=""),
            buyer_id=str(uuid4()),
            seller_id=str(uuid4()),
            chat_room_id=str(uuid4()),
            created_at=datetime.utcnow(),
        )
        assert response.status == DealStatus.PENDING


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
        message_id = str(uuid4())
        sender_id = str(uuid4())
        response = MessageResponse(
            id=message_id,
            sender_id=sender_id,
            sender_name="TestUser",
            content="Hello!",
            type="text",
            timestamp=datetime.utcnow(),
        )
        assert response.content == "Hello!"

    def test_chat_room_response(self):
        """Test chat room response schema."""
        room_id = str(uuid4())
        response = ChatRoomResponse(
            id=room_id,
            name="Test Room",
            type="private",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert response.type == "private"


class TestNotificationSchemas:
    """Test notification-related schemas."""

    def test_create_notification_request(self):
        """Test creating notification request."""
        from app.schemas.notification import NotificationType
        data = CreateNotificationRequest(
            user_id=uuid4(),
            title="Test",
            description="Test message",  # Field is 'description' not 'message'
            type=NotificationType.SYSTEM,
        )
        assert data.title == "Test"

    def test_notification_response(self):
        """Test notification response schema."""
        notif_id = uuid4()
        from app.schemas.notification import NotificationType
        response = NotificationResponse(
            id=notif_id,
            title="Test",
            description="Test message",  # Field is 'description' not 'message'
            type=NotificationType.SYSTEM,
            is_read=False,
            created_at=datetime.utcnow(),
            relative_time="just now",
        )
        assert response.type == NotificationType.SYSTEM


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
            vulnerabilities=[],
            recommendations=["Enable 2FA"],
            last_updated=datetime.utcnow(),
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
            featured_accounts=[],
            accounts=[],
            categories=[],
            pagination={"page": 1, "total": 0, "total_pages": 0, "has_next": False, "has_prev": False},
        )
        assert len(response.accounts) == 0

    def test_featured_accounts_response(self):
        """Test featured accounts response."""
        response = FeaturedAccountsResponse(
            accounts=[],
        )
        assert response.accounts == []


class TestAdminSchemas:
    """Test admin-related schemas."""

    def test_user_detail_response(self):
        """Test user detail response."""
        from app.schemas.admin import UserProfileInDetail, LoginHistoryItem
        from datetime import date

        user_id = uuid4()
        response = UserDetailResponse(
            id=str(user_id),
            username="admin",
            email="admin@example.com",
            phone="+1234567890",
            display_name="Admin",
            avatar_url=None,
            is_verified=True,
            is_email_verified=True,
            is_suspended=False,
            suspension_reason=None,
            is_banned=False,
            ban_reason=None,
            profile=UserProfileInDetail(
                bio=None,
                user_role="Trader",
                member_since=date.today(),
                completed_deals=0,
                rating=0.0,
                accounts_sold=0,
                bought_count=0,
            ),
            listings=0,
            active_deals=0,
            reports_against=0,
            login_history=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert response.username == "admin"

    def test_listing_moderation_response(self):
        """Test listing moderation response."""
        from app.schemas.admin import ListingInModeration, SellerInListing
        
        listing_id = uuid4()
        response = ListingModerationResponse(
            listings=[
                ListingInModeration(
                    id=str(listing_id),
                    title="Test Listing",
                    price=99.99,
                    game="Valorant",
                    seller=SellerInListing(
                        id=str(uuid4()),
                        username="seller123",
                        is_verified=False,
                    ),
                    status="pending",
                    image_urls=[],
                    created_at=datetime.utcnow(),
                    waiting_hours=2.5,
                )
            ],
            pagination={"page": 1, "total": 1, "total_pages": 1},
        )
        assert len(response.listings) == 1
        assert response.listings[0].title == "Test Listing"
