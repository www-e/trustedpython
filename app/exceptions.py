"""Custom exceptions for the application."""


class MarketplaceError(Exception):
    """Base exception for marketplace errors."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(MarketplaceError):
    """Resource not found."""

    def __init__(self, message: str):
        super().__init__(message, 404)


class ValidationError(MarketplaceError):
    """Invalid input data."""

    def __init__(self, message: str):
        super().__init__(message, 400)


class AuthenticationError(MarketplaceError):
    """Authentication failed."""

    def __init__(self, message: str):
        super().__init__(message, 401)


class ForbiddenError(MarketplaceError):
    """Access forbidden."""

    def __init__(self, message: str):
        super().__init__(message, 403)


class ConflictError(MarketplaceError):
    """Resource conflict."""

    def __init__(self, message: str):
        super().__init__(message, 409)


class RateLimitError(MarketplaceError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429)
