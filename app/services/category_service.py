"""Category service - business logic layer."""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError
)


class CategoryService:
    """Service for category-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize category service.

        Args:
            db: Database session
        """
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def create_category(self, category_data: CategoryCreate) -> Category:
        """
        Create a new category.

        Args:
            category_data: Category creation data

        Returns:
            Created category

        Raises:
            ConflictError: If category name already exists
            ValidationError: If data is invalid
        """
        # Check if category name already exists
        existing = await self.category_repo.get_by_name(category_data.name)
        if existing:
            raise ConflictError(f"Category '{category_data.name}' already exists")

        # Create category
        category = await self.category_repo.create(
            name=category_data.name,
            description=category_data.description,
            icon_url=category_data.icon_url,
            is_active=category_data.is_active,
            sort_order=category_data.sort_order
        )

        return category

    async def get_category(self, category_id: int) -> Category:
        """
        Get a category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category

        Raises:
            NotFoundError: If category not found
        """
        category = await self.category_repo.get(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")
        return category

    async def get_all_categories(
        self,
        active_only: bool = True,
        popular_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Get all categories.

        Args:
            active_only: Only return active categories
            popular_only: Only return popular categories (for home screen)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of categories
        """
        if popular_only:
            return await self.category_repo.get_popular_categories(skip, limit)
        if active_only:
            return await self.category_repo.get_active_categories(skip, limit)
        return await self.category_repo.get_all(skip, limit)

    async def update_category(
        self,
        category_id: int,
        category_data: CategoryUpdate
    ) -> Category:
        """
        Update a category.

        Args:
            category_id: Category ID
            category_data: Update data

        Returns:
            Updated category

        Raises:
            NotFoundError: If category not found
            ConflictError: If new name conflicts with existing category
        """
        # Check if category exists
        category = await self.category_repo.get(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # If updating name, check for conflicts
        if category_data.name and category_data.name != category.name:
            existing = await self.category_repo.get_by_name(category_data.name)
            if existing and existing.id != category_id:
                raise ConflictError(f"Category '{category_data.name}' already exists")

        # Build update dict with non-None values
        update_data = {
            k: v for k, v in category_data.model_dump().items()
            if v is not None
        }

        # Update category
        updated_category = await self.category_repo.update(category_id, **update_data)
        return updated_category

    async def delete_category(self, category_id: int) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValidationError: If category has listings
        """
        # Check if category exists
        category = await self.category_repo.get(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # Check if category has listings
        # TODO: Add listing count check when we have listings

        # Delete category
        return await self.category_repo.delete(category_id)

    async def search_categories(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Search categories by name.

        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching categories
        """
        return await self.category_repo.search_by_name(query, skip, limit)
