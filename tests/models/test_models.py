"""
Tests for SQLAlchemy models: user, account, listing, deal, chat, etc.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.models.user import User, UserProfile, Session, SecurityEvent, LoginHistory, TrustedDevice
from app.models.account import Account, AccountImage, AccountFeature
from app.models.listing import Listing
from app.models.deal import Deal, Payment
from app.models.chat import ChatRoom, ChatParticipant, Message, MessageAttachment
from app.models.notification import Notification, NotificationPreference
from app.models.review import Review
from app.models.mediator import Mediator, MediatorBadge, MediatorApplication, MediatorPaymentMethod
from app.models.content import Game, Category, PromoBanner, FAQItem


class TestUserModel:
    """Test User model."""

    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashed_password",
            is_email_verified=True,
            is_active=True,
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_user_default_values(self):
        """Test user model default values."""
        # Can't test defaults easily without DB - just verify model structure
        assert hasattr(User, "is_email_verified")
        assert hasattr(User, "is_active")
        assert hasattr(User, "is_suspended")
        assert hasattr(User, "two_factor_enabled")
        assert hasattr(User, "login_notifications")
        assert hasattr(User, "is_frozen")

    def test_user_relationships_exist(self):
        """Test user has expected relationships."""
        # Can't instantiate User without required fields, just check class attributes
        assert hasattr(User, "profile")
        assert hasattr(User, "sessions")
        assert hasattr(User, "accounts")
        assert hasattr(User, "listings")
        assert hasattr(User, "purchases")
        assert hasattr(User, "sales")
        assert hasattr(User, "mediated_deals")
        assert hasattr(User, "mediator_profile")
        assert hasattr(User, "chat_participations")
        assert hasattr(User, "sent_messages")
        assert hasattr(User, "notifications")
        assert hasattr(User, "notification_preferences")
        assert hasattr(User, "given_reviews")
        assert hasattr(User, "received_reviews")
        assert hasattr(User, "verified_payments")


class TestUserProfileModel:
    """Test UserProfile model."""

    def test_profile_creation(self):
        """Test creating a profile instance."""
        profile = UserProfile(
            id=uuid4(),
            user_id=uuid4(),
            display_name="Test User",
            bio="Test bio",
            user_role="Trader",
            is_verified=False,
        )
        assert profile.display_name == "Test User"
        assert profile.user_role == "Trader"

    def test_profile_default_values(self):
        """Test profile model defaults."""
        # Check defaults on class level
        assert UserProfile.user_role.default.arg == "Trader"
        assert UserProfile.is_verified.default.arg is False
        assert UserProfile.completed_deals.default.arg == 0


class TestSessionModel:
    """Test Session model."""

    def test_session_creation(self):
        """Test creating a session instance."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            access_token_hash="token_hash",
            refresh_token_hash="refresh_hash",
            expires_at=datetime.now(timezone.utc),
        )
        assert session.access_token_hash == "token_hash"
        assert session.user_id is not None


class TestSecurityEventModel:
    """Test SecurityEvent model."""

    def test_security_event_creation(self):
        """Test creating a security event."""
        event = SecurityEvent(
            id=uuid4(),
            user_id=uuid4(),
            event_type="login_success",
            ip_address="127.0.0.1",
        )
        assert event.event_type == "login_success"
        assert event.ip_address == "127.0.0.1"


class TestLoginHistoryModel:
    """Test LoginHistory model."""

    def test_login_history_creation(self):
        """Test creating login history record."""
        history = LoginHistory(
            id=uuid4(),
            user_id=uuid4(),
            ip_address="127.0.0.1",
            status="success",
        )
        assert history.status == "success"
        assert history.ip_address == "127.0.0.1"


class TestTrustedDeviceModel:
    """Test TrustedDevice model."""

    def test_trusted_device_creation(self):
        """Test creating trusted device."""
        device = TrustedDevice(
            id=uuid4(),
            user_id=uuid4(),
            device_name="Chrome on Windows",
            device_info="Mozilla/5.0...",
        )
        assert device.device_name == "Chrome on Windows"
        # Can't test is_active default without DB


class TestAccountModel:
    """Test Account model."""

    def test_account_creation(self):
        """Test creating an account instance."""
        account = Account(
            id=uuid4(),
            seller_id=uuid4(),
            title="Epic Gaming Account",
            price=99.99,
            game="Fortnite",
        )
        assert account.title == "Epic Gaming Account"
        assert account.price == 99.99

    def test_account_default_values(self):
        """Test account model defaults."""
        # Account model uses status field, not is_available
        assert Account.status.default.arg == "active"
        assert Account.views_count.default.arg == 0
        assert Account.is_featured.default.arg is False


class TestListingModel:
    """Test Listing model."""

    def test_listing_creation(self):
        """Test creating a listing instance."""
        listing = Listing(
            id=uuid4(),
            seller_id=uuid4(),
            title="Pro Account",
            price=149.99,
            game="Valorant",
            description="High rank account",
        )
        assert listing.title == "Pro Account"
        assert listing.price == 149.99

    def test_listing_default_values(self):
        """Test listing model defaults."""
        # Listing uses status field, not is_published
        assert Listing.status.default.arg == "draft"
        assert Listing.is_premium.default.arg is False
        assert Listing.views_count.default.arg == 0


class TestDealModel:
    """Test Deal model."""

    def test_deal_creation(self):
        """Test creating a deal instance."""
        deal = Deal(
            id=uuid4(),
            buyer_id=uuid4(),
            seller_id=uuid4(),
            status="pending",
            total_amount=99.99,
            currency="EGP",
        )
        assert deal.status == "pending"
        assert deal.total_amount == 99.99

    def test_deal_default_values(self):
        """Test deal model defaults."""
        # Deal has required fields (buyer_id, seller_id, total_amount), check class defaults
        assert Deal.status.default.arg == "pending"
        assert Deal.currency.default.arg == "EGP"


class TestPaymentModel:
    """Test Payment model."""

    def test_payment_creation(self):
        """Test creating a payment instance."""
        payment = Payment(
            id=uuid4(),
            deal_id=uuid4(),
            status="pending",
        )
        assert payment.status == "pending"

    def test_payment_default_values(self):
        """Test payment model defaults."""
        # Payment has required field deal_id, check class defaults
        assert Payment.status.default.arg == "pending"


class TestChatRoomModel:
    """Test ChatRoom model."""

    def test_chat_room_creation(self):
        """Test creating a chat room."""
        room = ChatRoom(
            id=uuid4(),
            type="private",
        )
        assert room.type == "private"
        # Can't test is_active default without DB

    def test_chat_room_default_values(self):
        """Test chat room defaults."""
        # ChatRoom has required field 'type', check class defaults
        assert ChatRoom.is_active.default.arg is True


class TestMessageModel:
    """Test Message model."""

    def test_message_creation(self):
        """Test creating a message."""
        message = Message(
            id=uuid4(),
            room_id=uuid4(),
            sender_id=uuid4(),
            content="Hello!",
            type="text",
        )
        assert message.content == "Hello!"
        assert message.type == "text"

    def test_message_default_values(self):
        """Test message defaults."""
        # Message has required fields, check class defaults
        assert Message.type.default.arg == "text"
        assert Message.is_deleted.default.arg is False


class TestNotificationModel:
    """Test Notification model."""

    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            description="Test message",  # Field is 'description', not 'message'
            type="info",
        )
        assert notification.title == "Test"
        assert notification.type == "info"

    def test_notification_default_values(self):
        """Test notification defaults."""
        # Notification has required fields, check class defaults
        assert Notification.is_read.default.arg is False


class TestMediatorModel:
    """Test Mediator model."""

    def test_mediator_creation(self):
        """Test creating a mediator."""
        mediator = Mediator(
            id=uuid4(),
            user_id=uuid4(),
            tier="gold",
            is_verified=True,
        )
        assert mediator.tier == "gold"
        assert mediator.is_verified is True

    def test_mediator_default_values(self):
        """Test mediator defaults."""
        # Mediator has required field user_id, check class defaults
        assert Mediator.rating.default.arg == 0.00
        assert Mediator.is_online.default.arg is True
        assert Mediator.tier.default.arg == "bronze"
        assert Mediator.is_verified.default.arg is False
        assert Mediator.is_active.default.arg is True


class TestReviewModel:
    """Test Review model."""

    def test_review_creation(self):
        """Test creating a review."""
        review = Review(
            id=uuid4(),
            reviewer_id=uuid4(),
            reviewee_id=uuid4(),
            rating=5,
            comment="Great seller!",
        )
        assert review.rating == 5
        assert review.comment == "Great seller!"


class TestGameModel:
    """Test Game model."""

    def test_game_creation(self):
        """Test creating a game."""
        game = Game(
            id=uuid4(),
            name="Fortnite",
            slug="fortnite",
        )
        assert game.name == "Fortnite"
        assert game.slug == "fortnite"

    def test_game_default_values(self):
        """Test game defaults."""
        assert Game.is_active.default.arg is True


class TestCategoryModel:
    """Test Category model."""

    def test_category_creation(self):
        """Test creating a category."""
        category = Category(
            id=uuid4(),
            name="Premium Accounts",
            slug="premium-accounts",
        )
        assert category.name == "Premium Accounts"

    def test_category_default_values(self):
        """Test category defaults."""
        assert Category.is_active.default.arg is True


class TestFAQItemModel:
    """Test FAQItem model."""

    def test_faq_creation(self):
        """Test creating an FAQ item."""
        faq = FAQItem(
            id=uuid4(),
            question="How do I buy?",
            answer="Click the buy button",
            display_order=1,  # Field is 'display_order', not 'order'
        )
        assert faq.question == "How do I buy?"
        assert faq.display_order == 1

    def test_faq_default_values(self):
        """Test FAQ defaults."""
        assert FAQItem.is_active.default.arg is True
        assert FAQItem.display_order.default.arg == 0


class TestPromoBannerModel:
    """Test PromoBanner model."""

    def test_promo_banner_creation(self):
        """Test creating a promo banner."""
        banner = PromoBanner(
            id=uuid4(),
            title="Summer Sale",
            image_url="https://example.com/banner.jpg",
            priority=1,
        )
        assert banner.title == "Summer Sale"
        assert banner.priority == 1

    def test_promo_banner_default_values(self):
        """Test promo banner defaults."""
        assert PromoBanner.is_active.default.arg is True
        assert PromoBanner.priority.default.arg == 0
