"""
SQLAlchemy models for the Game Account Marketplace.

This module imports all database models for easy access.
"""

# Account-related models
from app.models.account import Account, AccountFeature, AccountImage
from app.models.base import Base, TimestampMixin

# Chat-related models
from app.models.chat import ChatParticipant, ChatRoom, Message, MessageAttachment

# Content models
from app.models.content import Category, FAQItem, Game, PromoBanner

# Deal and Payment models
from app.models.deal import Deal, Payment

# Listing model
from app.models.listing import Listing

# Mediator-related models
from app.models.mediator import Mediator, MediatorBadge

# Notification-related models
from app.models.notification import Notification, NotificationPreference

# Review model
from app.models.review import Review

# User-related models
from app.models.user import Session, User, UserProfile

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # User models
    "User",
    "UserProfile",
    "Session",
    # Account models
    "Account",
    "AccountImage",
    "AccountFeature",
    # Listing model
    "Listing",
    # Deal models
    "Deal",
    "Payment",
    # Chat models
    "ChatRoom",
    "ChatParticipant",
    "Message",
    "MessageAttachment",
    # Notification models
    "Notification",
    "NotificationPreference",
    # Mediator models
    "Mediator",
    "MediatorBadge",
    # Review model
    "Review",
    # Content models
    "Game",
    "Category",
    "PromoBanner",
    "FAQItem",
]
