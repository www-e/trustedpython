"""User profile API endpoints."""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user_profile import (
    UserProfileResponse,
    UserProfileUpdate,
    PublicUserProfile,
    PasswordChange,
    UserStatsResponse,
)
from app.services.user_service import UserService
from app.exceptions import NotFoundError, ValidationError, ConflictError

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile."""
    try:
        user = await UserService(db).get_profile(current_user.id)
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    try:
        user = await UserService(db).update_profile(
            current_user.id,
            username=data.username,
            avatar_url=data.avatar_url,
            bio=data.bio,
        )
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/me/password")
async def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    try:
        await UserService(db).update_password_v2(
            current_user.id,
            data.current_password,
            data.new_password,
        )
        return {"message": "Password changed successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/stats", response_model=Dict)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's statistics."""
    try:
        stats = await UserService(db).get_user_stats(current_user.id)
        return stats
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}", response_model=PublicUserProfile)
async def get_public_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get public user profile (for other users to see)."""
    try:
        user = await UserService(db).get_profile(user_id)
        # Return only public fields
        return PublicUserProfile(
            id=user.id,
            username=user.username,
            avatar_url=user.avatar_url,
            bio=user.bio,
            rating=float(user.rating),
            completed_deals=user.completed_deals,
            is_verified=user.is_verified,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/stats", response_model=Dict)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get user statistics (public)."""
    try:
        stats = await UserService(db).get_user_stats(user_id)
        return stats
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me/trades")
async def get_my_trade_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's trade history.

    Returns deals where user was buyer or seller,
    ordered by most recent first.
    """
    try:
        trades = await UserService(db).get_trade_history(
            current_user.id,
            limit=limit,
            offset=offset
        )
        return {
            "items": trades,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(trades)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
