"""Category repository."""

from typing import List

from sqlalchemy import select, and_

from app.models.listing import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model."""

    def __init__(self, db):
        """
        Initialize category repository.

        Args:
            db: Database session
        """
        super().__init__(Category, db)

    async def get_active_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Get active categories.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active categories ordered by sort_order
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.sort_order, Category.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        """
        Get a category by name.

        Args:
            name: Category name

        Returns:
            Category instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def search_by_name(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Search categories by name (case-insensitive).

        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching categories
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.name.ilike(f"%{query}%"))
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_popular_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Get popular categories for home screen.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of popular categories ordered by sort_order
        """
        result = await self.db.execute(
            select(Category)
            .where(
                and_(
                    Category.is_active == True,
                    Category.is_popular == True
                )
            )
            .order_by(Category.sort_order, Category.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
