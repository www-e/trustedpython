"""Authentication endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_active_user
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User


# Response schemas
class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with phone number and password"
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    - **phone**: Unique phone number
    - **password**: Password (min 8 characters)
    - **role**: User role (buyer, seller, mediator, admin)
    """
    user_service = UserService(db)
    user = await user_service.register(user_data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate with phone number and password, receive JWT token"
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and receive JWT access token.

    - **phone**: Your registered phone number
    - **password**: Your password
    """
    user_service = UserService(db)
    result = await user_service.login(credentials.phone, credentials.password)

    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=UserResponse.model_validate(result["user"])
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user profile.

    Requires a valid JWT token in the Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout current user (client-side token removal)"
)
async def logout():
    """
    Logout user.

    Note: JWT tokens are stateless. Logout is handled client-side
    by removing the token. For server-side token invalidation,
    implement a token blacklist in Redis (future enhancement).
    """
    return None
