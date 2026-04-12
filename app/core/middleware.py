"""
Custom ASGI middleware for request tracking, timing, and error handling.

Provides RequestID for distributed tracing, TimingMiddleware for performance monitoring,
and global error handling middleware.
"""

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.exceptions import AppException

# ==============================================================================
# Request ID Middleware
# ==============================================================================


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request for tracing.

    The request ID is added to the request state and included in response headers.
    If client provides X-Request-ID header, it will be used; otherwise generates UUID.

    Attributes:
        app: ASGI application
        header_name: Header name for request ID (default: X-Request-ID)

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(RequestIDMiddleware)
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and add request ID.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response: Response with X-Request-ID header
        """
        # Get or generate request ID
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())

        # Store in request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.header_name] = request_id

        return response


# ==============================================================================
# Timing Middleware
# ==============================================================================


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks request processing time.

    Adds X-Process-Time header to responses showing milliseconds spent processing.
    Useful for performance monitoring and SLA tracking.

    Attributes:
        app: ASGI application
        header_name: Header name for timing (default: X-Process-Time)

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(TimingMiddleware)
        >>> # Response will include: X-Process-Time: 123.456
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Process-Time"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and track timing.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response: Response with X-Process-Time header
        """
        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time in milliseconds
        process_time_ms = (time.time() - start_time) * 1000

        # Add timing to response headers
        response.headers[self.header_name] = f"{process_time_ms:.3f}"

        return response


# ==============================================================================
# Error Handling Middleware
# ==============================================================================


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.

    Catches all exceptions and returns consistent JSON error responses.
    Handles AppException subclasses with proper status codes.

    Attributes:
        app: ASGI application
        debug: Whether to include detailed error stack traces (default: False)

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(ErrorHandlingMiddleware, debug=True)
    """

    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and handle any exceptions.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response: JSON error response if exception occurs, otherwise normal response
        """
        try:
            response = await call_next(request)
            return response

        except AppException as e:
            # Handle known application exceptions
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.error_code, "message": e.message, "status_code": e.status_code},
            )

        except ValueError as e:
            # Handle validation errors
            return JSONResponse(
                status_code=400,
                content={"error": "VALIDATION_ERROR", "message": str(e), "status_code": 400},
            )

        except PermissionError as e:
            # Handle permission errors
            return JSONResponse(
                status_code=403,
                content={
                    "error": "FORBIDDEN",
                    "message": str(e) or "Permission denied",
                    "status_code": 403,
                },
            )

        except Exception as e:
            # Handle unexpected errors
            if self.debug:
                # In debug mode, include full error details
                import traceback

                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "INTERNAL_ERROR",
                        "message": str(e),
                        "status_code": 500,
                        "traceback": traceback.format_exc(),
                    },
                )
            else:
                # In production, hide sensitive details
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "INTERNAL_ERROR",
                        "message": "An internal error occurred",
                        "status_code": 500,
                    },
                )


# ==============================================================================
# Logging Middleware (Optional)
# ==============================================================================


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs basic request information.

    Logs method, path, status code, and processing time for each request.
    Useful for basic access logging.

    Attributes:
        app: ASGI application
        logger: Optional logger instance (uses print if not provided)

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(LoggingMiddleware)
    """

    def __init__(self, app: ASGIApp, logger: Callable[[str], None] | None = None):
        super().__init__(app)
        self.logger = logger or print

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response: Normal response
        """
        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time_ms = (time.time() - start_time) * 1000

        # Get request ID if available
        request_id = getattr(request.state, "request_id", "-")

        # Log request details
        log_message = (
            f"[{request_id}] "
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} "
            f"({process_time_ms:.2f}ms)"
        )
        self.logger(log_message)

        return response
