"""
Rate limiting utilities for API endpoints.

Provides in-memory rate limiting using a simple dictionary-based approach.
For production, consider using Redis-based rate limiting.
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Tracks request counts per IP address within time windows.
    For production use, replace with Redis-based solution.

    Attributes:
        requests: Number of requests allowed per window
        window: Time window in seconds
        storage: Dictionary tracking requests per IP

    Example:
        >>> limiter = RateLimiter(requests=5, window=60)
        >>> limiter.check("192.168.1.1")  # Returns True if allowed
    """

    def __init__(self, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests: Number of requests allowed per time window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.storage: Dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for given key.

        Args:
            key: Unique identifier (e.g., IP address)

        Returns:
            Tuple[bool, int]: (allowed, retry_after_seconds)

        Example:
            >>> allowed, retry_after = limiter.check("192.168.1.1")
            >>> if not allowed:
            ...     print(f"Try again in {retry_after} seconds")
        """
        now = time.time()

        # Get existing requests for this key
        requests = self.storage[key]

        # Remove expired requests outside the window
        self.storage[key] = [t for t in requests if t > now - self.window]
        requests = self.storage[key]

        # Check if limit exceeded
        if len(requests) >= self.requests:
            # Calculate retry after time
            oldest_request = min(requests)
            retry_after = int(oldest_request + self.window - now) + 1
            return False, retry_after

        # Add current request
        self.storage[key].append(now)
        return True, 0

    def reset(self, key: str) -> None:
        """
        Reset rate limit for a specific key.

        Args:
            key: Unique identifier to reset

        Example:
            >>> limiter.reset("192.168.1.1")
        """
        if key in self.storage:
            del self.storage[key]


# Global rate limiter instances
login_limiter = RateLimiter(requests=5, window=60)  # 5 login attempts per minute
register_limiter = RateLimiter(requests=3, window=60)  # 3 registrations per minute
general_limiter = RateLimiter(requests=100, window=60)  # 100 requests per minute
chat_message_limiter = RateLimiter(requests=100, window=60)  # 100 messages per minute


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Handles proxy headers (X-Forwarded-For, X-Real-IP).

    Args:
        request: FastAPI request

    Returns:
        str: Client IP address

    Example:
        >>> ip = get_client_ip(request)
        >>> print(f"Request from: {ip}")
    """
    # Check for forwarded headers (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get first IP in chain
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection IP
    if request.client:
        return request.client.host

    return "unknown"


async def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """
    Async rate limiting function using Redis.

    Args:
        key: Unique identifier for rate limit (e.g., "user_123", "ip_192.168.1.1")
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Returns:
        bool: True if request is allowed, False if rate limit exceeded

    Example:
        >>> if await check_rate_limit("user_123", max_requests=10, window_seconds=60):
        ...     # Process request
        ... else:
        ...     # Rate limit exceeded
    """
    try:
        from app.core.redis import get_redis

        redis_client = await get_redis()

        if not redis_client:
            # If Redis unavailable, allow request (fail open)
            return True

        # Use Redis INCR with expiration for sliding window
        rate_key = f"rate_limit:{key}"

        # Increment counter
        current = await redis_client.incr(rate_key)

        # Set expiration on first request
        if current == 1:
            await redis_client.expire(rate_key, window_seconds)

        # Check if limit exceeded
        allowed: bool = current <= max_requests
        return allowed

    except Exception as e:
        # On error, allow request (fail open)
        import logging

        logging.getLogger(__name__).error(f"Rate limit check failed: {e}")
        return True


def rate_limit(
    requests: int = 100, window: int = 60, limiter: RateLimiter | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Rate limiting decorator for endpoint functions.

    Args:
        requests: Number of requests allowed per window
        window: Time window in seconds
        limiter: Optional custom rate limiter instance

    Returns:
        Decorator function

    Example:
        >>> @router.post("/login")
        ... @rate_limit(requests=5, window=60)
        ... async def login(...):
        ...     pass
    """
    if limiter is None:
        limiter = RateLimiter(requests=requests, window=window)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find Request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                # Try to get from kwargs
                request = kwargs.get("request")

            if request:
                # Get client IP
                client_ip = get_client_ip(request)

                # Check rate limit
                allowed, retry_after = limiter.check(client_ip)

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Try again in {retry_after} seconds",
                            "retry_after": retry_after,
                        },
                        headers={"Retry-After": str(retry_after)},
                    )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit_login(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Rate limiting decorator for login endpoint (5 attempts per minute).

    Args:
        func: Endpoint function to decorate

    Example:
        >>> @router.post("/login")
        ... @rate_limit_login
        ... async def login(...):
        ...     pass
    """
    return rate_limit(limiter=login_limiter)(func)


def rate_limit_register(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Rate limiting decorator for register endpoint (3 attempts per minute).

    Args:
        func: Endpoint function to decorate

    Example:
        >>> @router.post("/register")
        ... @rate_limit_register
        ... async def register(...):
        ...     pass
    """
    return rate_limit(limiter=register_limiter)(func)


def rate_limit_chat_message(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Rate limiting decorator for chat messages (100 messages per minute).

    Args:
        func: Endpoint function to decorate

    Example:
        >>> @router.post("/rooms/{id}/messages")
        ... @rate_limit_chat_message
        ... async def send_message(...):
        ...     pass
    """
    return rate_limit(limiter=chat_message_limiter)(func)
