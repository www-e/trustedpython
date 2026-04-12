"""
Application constants and enumerations.

Provides enums and constants for consistent type-safe values across the application.
"""

from enum import Enum
from typing import Final

# ==============================================================================
# User Enums
# ==============================================================================


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class UserRole(str, Enum):
    """User role in the system."""

    BUYER = "buyer"
    SELLER = "seller"
    MEDIATOR = "mediator"
    ADMIN = "admin"


# ==============================================================================
# Deal & Transaction Enums
# ==============================================================================


class DealStatus(str, Enum):
    """Status of a deal transaction."""

    PENDING = "pending"  # Initial state, awaiting payment
    AWAITING_PAYMENT = "awaiting_payment"  # Payment initiated, waiting for confirmation
    PAYMENT_SUBMITTED = "payment_submitted"  # Buyer provided payment proof
    VERIFIED = "verified"  # Payment verified by mediator
    COMPLETED = "completed"  # Deal successfully finished
    CANCELLED = "cancelled"  # Deal cancelled
    DISPUTED = "disputed"  # Dispute opened


class PaymentStatus(str, Enum):
    """Payment verification status."""

    PENDING = "pending"  # Awaiting verification
    SUBMITTED = "submitted"  # Payment proof submitted
    VERIFIED = "verified"  # Payment verified by mediator
    REJECTED = "rejected"  # Payment proof rejected


# ==============================================================================
# Listing Enums
# ==============================================================================


class ListingStatus(str, Enum):
    """Listing status."""

    DRAFT = "draft"  # Not yet published
    ACTIVE = "active"  # Visible and available
    SOLD = "sold"  # Account sold
    EXPIRED = "expired"  # Listing expired


class ListingSort(str, Enum):
    """Listing sort options."""

    NEWEST = "newest"
    PRICE_LOW = "price_low"
    PRICE_HIGH = "price_high"
    RATING = "rating"


# ==============================================================================
# Chat & Messaging Enums
# ==============================================================================


class ChatType(str, Enum):
    """Type of chat conversation."""

    PRIVATE = "private"  # One-to-one chat
    GROUP = "group"  # Deal group chat (buyer, seller, mediator)


class MessageType(str, Enum):
    """Type of message in chat."""

    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"  # Automated messages (deal updates, etc.)


# ==============================================================================
# Notification Enums
# ==============================================================================


class NotificationType(str, Enum):
    """Notification category."""

    ACCOUNT_UPDATE = "account_update"  # Listing/account changes
    MESSAGE = "message"  # New chat messages
    SECURITY_ALERT = "security_alert"  # Security events
    PURCHASE = "purchase"  # Purchase events
    SYSTEM = "system"  # System announcements


# ==============================================================================
# Mediator Enums
# ==============================================================================


class MediatorTier(str, Enum):
    """Mediator experience/certification level."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ELITE = "elite"


# ==============================================================================
# Pagination & Limits
# ==============================================================================

# Default values (can be overridden by config)
DEFAULT_PAGE_SIZE: Final[int] = 20
DEFAULT_PAGE: Final[int] = 1
MAX_PAGE_SIZE: Final[int] = 100
MIN_PAGE_SIZE: Final[int] = 1

# Search limits
MAX_SEARCH_RESULTS: Final[int] = 1000
MIN_SEARCH_LENGTH: Final[int] = 2

# Rate limiting
RATE_LIMIT_REQUESTS: Final[int] = 100
RATE_LIMIT_PERIOD_SECONDS: Final[int] = 60

# File upload
MAX_FILE_SIZE_MB: Final[int] = 10
ALLOWED_IMAGE_EXTENSIONS: Final[set[str]] = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGES_PER_LISTING: Final[int] = 10

# ==============================================================================
# Fees & Pricing
# ==============================================================================

PLATFORM_FEE_PERCENTAGE: Final[float] = 5.0  # Platform fee on transactions
MEDIATOR_FEE_PERCENTAGE: Final[float] = 2.0  # Mediator fee on transactions
MIN_DEAL_AMOUNT: Final[float] = 1.0  # Minimum deal amount
MAX_DEAL_AMOUNT: Final[float] = 10000.0  # Maximum deal amount

# ==============================================================================
# Time Limits
# ==============================================================================

# Token expiration (in seconds, matches config)
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7

# Deal timeouts (in hours)
PAYMENT_TIMEOUT_HOURS: Final[int] = 24  # Time to submit payment
VERIFICATION_TIMEOUT_HOURS: Final[int] = 48  # Time for mediator to verify
COMPLETION_TIMEOUT_DAYS: Final[int] = 7  # Time to complete deal after payment

# Listing expiration
LISTING_EXPIRY_DAYS: Final[int] = 30  # Auto-expire listings after 30 days

# ==============================================================================
# Cache Keys
# ==============================================================================


class CacheKey(str, Enum):
    """Redis cache key patterns."""

    USER_SESSION = "session:user:{user_id}"
    USER_LISTINGS = "listings:user:{user_id}"
    LISTING_DETAIL = "listing:{listing_id}"
    DEAL_CACHE = "deal:{deal_id}"
    RATE_LIMIT = "ratelimit:{user_id}:{endpoint}"
    SEARCH_RESULTS = "search:{query_hash}"


# Cache TTL (in seconds)
CACHE_TTL_SECONDS: Final[int] = 3600  # 1 hour
SESSION_TTL_SECONDS: Final[int] = 604800  # 7 days

# ==============================================================================
# Email Templates
# ==============================================================================


class EmailTemplate(str, Enum):
    """Email template types."""

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    DEAL_UPDATE = "deal_update"
    SECURITY_ALERT = "security_alert"


# ==============================================================================
# Validation Rules
# ==============================================================================

# Password requirements
MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 128
PASSWORD_REQUIRE_UPPERCASE: Final[bool] = True
PASSWORD_REQUIRE_LOWERCASE: Final[bool] = True
PASSWORD_REQUIRE_NUMBER: Final[bool] = True
PASSWORD_REQUIRE_SPECIAL: Final[bool] = True

# Username requirements
MIN_USERNAME_LENGTH: Final[int] = 3
MAX_USERNAME_LENGTH: Final[int] = 30
USERNAME_PATTERN: Final[str] = r"^[a-zA-Z0-9_-]+$"

# URL slug requirements
MIN_SLUG_LENGTH: Final[int] = 3
MAX_SLUG_LENGTH: Final[int] = 50
SLUG_PATTERN: Final[str] = r"^[a-z0-9-]+$"
