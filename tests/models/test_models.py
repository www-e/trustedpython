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
        user = User()
        assert user.is_email_verified is False
        assert user.is_active is True
        assert user.is_suspended is False
        assert user.two_factor_enabled is False
        assert user.login_notifications is True
        assert user.is_frozen is False

    def test_user_relationships_exist(self):
        """Test user has expected relationships."""
        user = User()
        assert hasattr(user, "profile")
        assert hasattr(user, "sessions")
        assert hasattr(user, "accounts")
        assert hasattr(user, "listings")
        assert hasattr(user, "purchases")
        assert hasattr(user, "sales")
        assert hasattr(user, "mediated_deals")
        assert hasattr(user, "mediator_profile")
        assert hasattr(user, "chat_participations")
        assert hasattr(user, "sent_messages")
        assert hasattr(user, "notifications")
        assert hasattr(user, "notification_preferences")
        assert hasattr(user, "given_reviews")
        assert hasattr(user, "received_reviews")
        assert hasattr(user, "verified_payments")


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
        """Test profile model default values."""
        profile = UserProfile()
        assert profile.user_role == "Trader"
        assert profile.is_verified is False
        assert profile.completed_deals == 0
        assert profile.rating == 0.00
        assert profile.accounts_sold == 0


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
        assert device.is_active is True


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
        account = Account()
        assert account.is_available is True
        assert account.views_count == 0
        assert account.is_featured is False


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
        listing = Listing()
        assert listing.is_published is False
        assert listing.is_premium is False
        assert listing.views_count == 0


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
        deal = Deal()
        assert deal.status == "pending"
        assert deal.currency == "EGP"


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
        payment = Payment()
        assert payment.status == "pending"


class TestChatRoomModel:
    """Test ChatRoom model."""

    def test_chat_room_creation(self):
        """Test creating a chat room."""
        room = ChatRoom(
            id=uuid4(),
            type="private",
        )
        assert room.type == "private"
        assert room.is_active is True

    def test_chat_room_default_values(self):
        """Test chat room defaults."""
        room = ChatRoom()
        assert room.is_active is True


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
        message = Message()
        assert message.type == "text"
        assert message.is_deleted is False


class TestNotificationModel:
    """Test Notification model."""

    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            message="Test message",
            type="info",
        )
        assert notification.title == "Test"
        assert notification.type == "info"

    def test_notification_default_values(self):
        """Test notification defaults."""
        notification = Notification()
        assert notification.is_read is False
        assert notification.type == "info"


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
        mediator = Mediator()
        assert mediator.rating == 0.00
        assert mediator.is_online is True
        assert mediator.tier == "bronze"
        assert mediator.is_verified is False
        assert mediator.is_active is True


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
        game = Game()
        assert game.is_active is True


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
        category = Category()
        assert category.is_active is True


class TestFAQItemModel:
    """Test FAQItem model."""

    def test_faq_creation(self):
        """Test creating an FAQ item."""
        faq = FAQItem(
            id=uuid4(),
            question="How do I buy?",
            answer="Click the buy button",
            order=1,
        )
        assert faq.question == "How do I buy?"
        assert faq.order == 1

    def test_faq_default_values(self):
        """Test FAQ defaults."""
        faq = FAQItem()
        assert faq.is_active is True
        assert faq.order == 0


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
        banner = PromoBanner()
        assert banner.is_active is True
        assert banner.priority == 0
