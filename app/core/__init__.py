"""
Core module - Configuration, security, exceptions, middleware, and constants.

This module provides the foundational infrastructure for the Game Account Marketplace:
- Configuration management with environment variables
- Security utilities (password hashing, JWT tokens)
- Custom exception classes with error codes
- ASGI middleware (request ID, timing, error handling)
- Application constants and enumerations
"""

from app.core.config import Settings, get_settings, settings
from app.core.constants import (
    CacheKey,
    ChatType,
    DealStatus,
    EmailTemplate,
    ListingSort,
    ListingStatus,
    MediatorTier,
    MessageType,
    NotificationType,
    PaymentStatus,
    UserRole,
    UserStatus,
)
from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    PaymentRequiredException,
    RateLimitException,
    ServiceUnavailableException,
    UnauthorizedException,
    ValidationException,
)
from app.core.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_token,
)

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    "settings",
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    # Exceptions
    "AppException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ValidationException",
    "ConflictException",
    "RateLimitException",
    "PaymentRequiredException",
    "InternalServerException",
    "ServiceUnavailableException",
    # Middleware
    "RequestIDMiddleware",
    "TimingMiddleware",
    "ErrorHandlingMiddleware",
    "LoggingMiddleware",
    # Constants & Enums
    "UserStatus",
    "UserRole",
    "DealStatus",
    "PaymentStatus",
    "ListingStatus",
    "ListingSort",
    "ChatType",
    "MessageType",
    "NotificationType",
    "MediatorTier",
    "EmailTemplate",
    "CacheKey",
]
