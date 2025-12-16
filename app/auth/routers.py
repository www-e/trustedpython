from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.core import get_async_session
from app.models.user import (
    User, UserRegistration, UserLogin, Token, 
    TokenData, RefreshTokenRequest, UserState, UserRole
)
from app.auth.utils import (
    create_access_token, create_refresh_token, 
    verify_token, require_admin, require_approved_user
)
from datetime import timedelta
from typing import Optional

auth_router = APIRouter()

@auth_router.post("/register", response_model=Token)
async def register(user_registration: UserRegistration, db: AsyncSession = Depends(get_async_session)):
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_registration.username))
    existing_user = result.first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    # Determine user state based on role
    if user_registration.role == UserRole.MEDIATOR:
        user_state = UserState.PENDING
    elif user_registration.role == UserRole.REGULAR_USER:
        user_state = UserState.APPROVED  # Auto-approved
    else:
        user_state = UserState.PENDING  # Default
    
    # Create new user
    user = User(
        username=user_registration.username,
        phone_number=user_registration.phone_number,
        second_phone_number=user_registration.second_phone_number,
        account_info=user_registration.account_info,
        role=user_registration.role,
        state=user_state
    )
    user.set_password(user_registration.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    access_token_expires = timedelta(minutes=30)
    refresh_token_expires = timedelta(days=7)
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "state": user.state.value,
            "user_id": user.id
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id
        },
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        state=user.state
    )

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    # Find user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.first()
    
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.state != UserState.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not approved. Please contact administrator."
        )
    
    # Generate tokens
    access_token_expires = timedelta(minutes=30)
    refresh_token_expires = timedelta(days=7)
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "state": user.state.value,
            "user_id": user.id
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id
        },
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        state=user.state
    )

@auth_router.post("/token/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_session)):
    # Verify refresh token
    token_data = verify_token(refresh_request.refresh_token)
    
    if not token_data or "type" not in token_data.__dict__ or getattr(token_data, 'type', None) != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.state != UserState.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not approved. Cannot refresh token."
        )
    
    # Generate new tokens
    access_token_expires = timedelta(minutes=30)
    refresh_token_expires = timedelta(days=7)
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "state": user.state.value,
            "user_id": user.id
        },
        expires_delta=access_token_expires
    )
    
    # Optionally generate a new refresh token
    new_refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id
        },
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        state=user.state
    )

@auth_router.get("/me", response_model=TokenData)
async def get_current_user_info(current_user: User = Depends(require_approved_user)):
    return TokenData(
        username=current_user.username,
        role=current_user.role,
        state=current_user.state
    )