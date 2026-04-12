"""API route dependencies."""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db as async_get_db
from app.core.redis import get_redis as async_get_redis
from app.core.security import decode_token
from app.models.user import User

# Security
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async for session in async_get_db():
        yield session


async def get_redis() -> Redis | None:
    """Get Redis client."""
    return await async_get_redis()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Get user from database
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    limit: int = Field(20, ge=1, le=100, description="Items per page (max 100)")


async def paginate(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """
    Get pagination parameters.

    Args:
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        PaginationParams: Pagination parameters
    """
    return PaginationParams(page=page, limit=limit)


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationMeta":
        """
        Create pagination metadata.

        Args:
            page: Current page number
            limit: Items per page
            total: Total number of items

        Returns:
            PaginationMeta: Pagination metadata
        """
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.

    Args:
        credentials: HTTP Bearer credentials (optional)
        db: Database session

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
