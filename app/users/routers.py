from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.database.core import get_async_session
from app.models.user import User, UserState, UserRole, UserApprovalRequest, UserUpdateRequest
from app.auth.utils import require_admin, require_approved_user, get_current_user
from typing import List

users_router = APIRouter()

@users_router.get("/", response_model=List[dict])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    admin_user: User = Depends(require_admin)
):
    """
    Get all users (admin only)
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "phone_number": user.phone_number,
            "second_phone_number": user.second_phone_number,
            "account_info": user.account_info,
            "role": user.role,
            "state": user.state,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        for user in users
    ]

@users_router.get("/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    admin_user: User = Depends(require_admin)
):
    """
    Get a specific user by ID (admin only)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "phone_number": user.phone_number,
        "second_phone_number": user.second_phone_number,
        "account_info": user.account_info,
        "role": user.role,
        "state": user.state,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@users_router.put("/{user_id}/approve", response_model=dict)
async def approve_user(
    user_id: int,
    approval_request: UserApprovalRequest,
    db: AsyncSession = Depends(get_async_session),
    admin_user: User = Depends(require_admin)
):
    """
    Approve or reject a user (admin only)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from approving themselves in this endpoint
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve yourself"
        )
    
    # Update user state based on approval request
    if approval_request.approve:
        user.state = UserState.APPROVED
    else:
        user.state = UserState.REJECTED
    
    user.updated_at = user.updated_at.now()  # Fixed: use now() method
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "state": user.state,
        "updated_at": user.updated_at
    }

@users_router.put("/profile", response_model=dict)
async def update_own_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(require_approved_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update own profile information (authenticated users)
    """
    # Update fields only if they are provided in the request
    if update_data.phone_number is not None:
        current_user.phone_number = update_data.phone_number
    if update_data.second_phone_number is not None:
        current_user.second_phone_number = update_data.second_phone_number
    if update_data.account_info is not None:
        current_user.account_info = update_data.account_info
    
    current_user.updated_at = datetime.utcnow()  # Fixed: import datetime
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "phone_number": current_user.phone_number,
        "second_phone_number": current_user.second_phone_number,
        "account_info": current_user.account_info,
        "role": current_user.role,
        "state": current_user.state,
        "updated_at": current_user.updated_at
    }

from datetime import datetime  # Added this import at the end since it was missing