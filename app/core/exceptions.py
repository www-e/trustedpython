"""Exception handlers for FastAPI."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    MarketplaceError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ForbiddenError,
    ConflictError,
    RateLimitError
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers for the FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        """Handle NotFoundError."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "not_found",
                "message": exc.message
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle ValidationError."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "validation_error",
                "message": exc.message
            }
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request,
        exc: AuthenticationError
    ):
        """Handle AuthenticationError."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "authentication_failed",
                "message": exc.message
            }
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError):
        """Handle ForbiddenError."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "forbidden",
                "message": exc.message
            }
        )

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError):
        """Handle ConflictError."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "conflict",
                "message": exc.message
            }
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitError):
        """Handle RateLimitError."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": exc.message
            }
        )

    @app.exception_handler(MarketplaceError)
    async def marketplace_error_handler(request: Request, exc: MarketplaceError):
        """Handle generic MarketplaceError."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "server_error",
                "message": exc.message
            }
        )
