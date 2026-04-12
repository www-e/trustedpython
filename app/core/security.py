"""
Security utilities for authentication and password management.

Provides password hashing, JWT token creation/validation, and related security functions.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password

    Example:
        >>> hashed = hash_password("myPassword123!")
        >>> isinstance(hashed, str)
        True
    """
    hashed: str = pwd_context.hash(password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("myPassword123!")
        >>> verify_password("myPassword123!", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user_123"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    # Encode JWT
    token: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Payload data to encode in the token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time. Defaults to REFRESH_TOKEN_EXPIRE_DAYS

    Returns:
        str: Encoded JWT refresh token

    Example:
        >>> token = create_refresh_token({"sub": "user_123"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()

    # Set expiration time (longer than access token)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    # Encode JWT
    token: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Optional[dict]: Decoded token payload if valid, None if invalid

    Example:
        >>> token = create_access_token({"sub": "user_123"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user_123'
        >>> decode_token("invalid")
        None
    """
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT token with type checking.

    Args:
        token: JWT token to decode
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[dict]: Decoded token payload if valid and correct type, None otherwise

    Example:
        >>> access = create_access_token({"sub": "user_123"})
        >>> verify_token(access, "access")["sub"]
        'user_123'
        >>> verify_token(access, "refresh") is None
        True
    """
    payload = decode_token(token)

    if payload is None:
        return None

    # Verify token type
    if payload.get("type") != token_type:
        return None

    return payload
