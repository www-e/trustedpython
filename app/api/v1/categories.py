"""Category endpoints."""

from typing import List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.models.user import User
from app.models.enums import UserRole

router = APIRouter()


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new game category (admin only)"
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new category.

    Requires admin role.
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only admins can create categories")

    service = CategoryService(db)
    category = await service.create_category(category_data)
    return CategoryResponse.model_validate(category)


@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="Get all categories",
    description="Get list of all active categories"
)
async def get_categories(
    active_only: bool = Query(True, description="Only show active categories"),
    popular_only: bool = Query(False, description="Only show popular categories (for home screen)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all categories.

    Query parameters:
    - active_only: Only return active categories (default: true)
    - popular_only: Only return popular categories (for home screen popular games section)
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (pagination)
    """
    service = CategoryService(db)
    categories = await service.get_all_categories(active_only, popular_only, skip, limit)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get(
    "/categories/search",
    response_model=List[CategoryResponse],
    summary="Search categories",
    description="Search categories by name"
)
async def search_categories(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search categories by name.

    Query parameters:
    - q: Search query for category name
    - skip: Number of records to skip
    - limit: Maximum records to return
    """
    service = CategoryService(db)
    categories = await service.search_categories(q, skip, limit)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
    description="Get a specific category by ID"
)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a category by ID.

    Returns category details including listings count.
    """
    service = CategoryService(db)
    category = await service.get_category(category_id)
    return CategoryResponse.model_validate(category)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
    description="Update category details (admin only)"
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a category.

    Requires admin role.
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only admins can update categories")

    service = CategoryService(db)
    category = await service.update_category(category_id, category_data)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description="Delete a category (admin only)"
)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a category.

    Requires admin role. Cannot delete categories with active listings.
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("Only admins can delete categories")

    service = CategoryService(db)
    await service.delete_category(category_id)
    return None
