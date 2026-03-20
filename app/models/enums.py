"""Enumerations for database models."""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    BUYER = "buyer"
    SELLER = "seller"
    MEDIATOR = "mediator"
    ADMIN = "admin"


class ListingStatus(str, Enum):
    """Listing status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"  # Awaiting admin approval
    ACTIVE = "active"
    SOLD = "sold"
    PAUSED = "paused"
    ARCHIVED = "archived"


class GameType(str, Enum):
    """Game type enumeration."""

    PUBG = "pubg"
    FREE_FIRE = "free_fire"
    CALL_OF_DUTY = "call_of_duty"
    FORTNITE = "fortnite"
    MOBILE_LEGENDS = "mobile_legends"
    OTHER = "other"


class DealStatus(str, Enum):
    """Deal status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_VERIFIED = "payment_verified"
    CREDENTIALS_EXCHANGED = "credentials_exchanged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
