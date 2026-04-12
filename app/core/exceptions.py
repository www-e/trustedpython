"""
Custom exception classes for the application.

Provides typed exceptions with error codes and messages for consistent error handling.
"""

from typing import Optional


class AppException(Exception):
    """
    Base exception class for all application errors.

    Attributes:
        error_code: Unique error code for this type of error
        message: Human-readable error message
        status_code: HTTP status code (default: 500)

    Example:
        >>> raise AppException("CUSTOM_ERROR", "Something went wrong", 500)
    """

    def __init__(self, error_code: str, message: str, status_code: int = 500):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """
    Exception raised when a resource is not found (404).

    Example:
        >>> raise NotFoundException("user_123")
        NotFoundException: Resource 'user_123' not found
    """

    def __init__(self, resource_id: str, resource_type: str = "Resource"):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource_type} '{resource_id}' not found",
            status_code=404,
        )


class UnauthorizedException(AppException):
    """
    Exception raised when authentication is required but missing/invalid (401).

    Example:
        >>> raise UnauthorizedException()
        UnauthorizedException: Authentication required
    """

    def __init__(self, message: str = "Authentication required"):
        super().__init__(error_code="UNAUTHORIZED", message=message, status_code=401)


class ForbiddenException(AppException):
    """
    Exception raised when user lacks permission for an action (403).

    Example:
        >>> raise ForbiddenException("delete accounts")
        ForbiddenException: You don't have permission to delete accounts
    """

    def __init__(self, action: str = "perform this action"):
        super().__init__(
            error_code="FORBIDDEN",
            message=f"You don't have permission to {action}",
            status_code=403,
        )


class ValidationException(AppException):
    """
    Exception raised when request validation fails (400).

    Args:
        message: Validation error message
        field: Optional field name that failed validation

    Example:
        >>> raise ValidationException("Email is invalid", "email")
        ValidationException: Invalid field 'email': Email is invalid
    """

    def __init__(self, message: str, field: Optional[str] = None):
        if field:
            message = f"Invalid field '{field}': {message}"

        super().__init__(error_code="VALIDATION_ERROR", message=message, status_code=400)


class ConflictException(AppException):
    """
    Exception raised when a request conflicts with existing state (409).

    Example:
        >>> raise ConflictException("email", "user@example.com")
        ConflictException: email 'user@example.com' already exists
    """

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            error_code="CONFLICT",
            message=f"{resource_type} '{resource_id}' already exists",
            status_code=409,
        )


class RateLimitException(AppException):
    """
    Exception raised when rate limit is exceeded (429).

    Args:
        retry_after: Optional seconds until client can retry

    Example:
        >>> raise RateLimitException(60)
        RateLimitException: Rate limit exceeded. Try again in 60 seconds
    """

    def __init__(self, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Try again in {retry_after} seconds"

        super().__init__(error_code="RATE_LIMIT_EXCEEDED", message=message, status_code=429)


class PaymentRequiredException(AppException):
    """
    Exception raised when payment is required for an action (402).

    Example:
        >>> raise PaymentRequiredException(100.00, "USD")
        PaymentRequiredException: Payment required: $100.00 USD
    """

    def __init__(self, amount: float, currency: str = "USD"):
        super().__init__(
            error_code="PAYMENT_REQUIRED",
            message=f"Payment required: ${amount:.2f} {currency}",
            status_code=402,
        )


class InternalServerException(AppException):
    """
    Exception raised for unexpected server errors (500).

    Example:
        >>> raise InternalServerException("Database connection failed")
        InternalServerException: An internal error occurred: Database connection failed
    """

    def __init__(self, message: str = "An internal error occurred"):
        super().__init__(error_code="INTERNAL_ERROR", message=message, status_code=500)


class ServiceUnavailableException(AppException):
    """
    Exception raised when a service is temporarily unavailable (503).

    Example:
        >>> raise ServiceUnavailableException("Payment gateway")
        ServiceUnavailableException: Payment gateway is currently unavailable
    """

    def __init__(self, service_name: str = "Service"):
        super().__init__(
            error_code="SERVICE_UNAVAILABLE",
            message=f"{service_name} is currently unavailable. Please try again later",
            status_code=503,
        )


# Convenience aliases for commonly used exceptions
NotFoundError = NotFoundException
ForbiddenError = ForbiddenException
ValidationError = ValidationException
UnauthorizedError = UnauthorizedException
ConflictError = ConflictException
RateLimitError = RateLimitException
