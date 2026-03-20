"""Listing repository."""

from typing import List, Tuple
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.models.listing import Listing, ListingImage
from app.models.enums import ListingStatus
from app.repositories.base import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    """Repository for Listing model."""

    def __init__(self, db):
        """
        Initialize listing repository.

        Args:
            db: Database session
        """
        super().__init__(Listing, db)

    async def get_with_images(self, listing_id: int) -> Listing | None:
        """
        Get a listing by ID with images preloaded.

        Args:
            listing_id: Listing ID

        Returns:
            Listing instance with images if found, None otherwise
        """
        result = await self.db.execute(
            select(Listing)
            .options(selectinload(Listing.images))
            .where(Listing.id == listing_id)
        )
        return result.scalar_one_or_none()

    async def get_by_seller(
        self,
        seller_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Get listings by seller ID.

        Args:
            seller_id: Seller user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of seller's listings
        """
        result = await self.db.execute(
            select(Listing)
            .where(Listing.seller_id == seller_id)
            .order_by(desc(Listing.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Get listings by category ID.

        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of listings in the category
        """
        result = await self.db.execute(
            select(Listing)
            .where(Listing.category_id == category_id)
            .order_by(desc(Listing.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_listings(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Get active listings.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active listings ordered by featured first, then newest
        """
        result = await self.db.execute(
            select(Listing)
            .where(Listing.status == ListingStatus.ACTIVE)
            .order_by(desc(Listing.is_featured), desc(Listing.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        category_id: int | None = None,
        game_type: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """
        Search listings with filters.

        Args:
            query: Search query for title/description
            category_id: Filter by category
            game_type: Filter by game type
            min_price: Minimum price
            max_price: Maximum price
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching listings
        """
        conditions = [Listing.status == ListingStatus.ACTIVE]

        # Text search
        if query:
            conditions.append(
                or_(
                    Listing.title.ilike(f"%{query}%"),
                    Listing.description.ilike(f"%{query}%")
                )
            )

        # Category filter
        if category_id:
            conditions.append(Listing.category_id == category_id)

        # Game type filter
        if game_type:
            conditions.append(Listing.game_type == game_type)

        # Price range
        if min_price:
            conditions.append(Listing.price >= min_price)
        if max_price:
            conditions.append(Listing.price <= max_price)

        result = await self.db.execute(
            select(Listing)
            .where(and_(*conditions))
            .order_by(desc(Listing.is_featured), desc(Listing.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_featured_listings(
        self,
        limit: int = 10
    ) -> List[Listing]:
        """
        Get featured listings.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of featured active listings
        """
        result = await self.db.execute(
            select(Listing)
            .where(
                and_(
                    Listing.status == ListingStatus.ACTIVE,
                    Listing.is_featured == True
                )
            )
            .order_by(desc(Listing.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def increment_views(self, listing_id: int) -> bool:
        """
        Increment listing view count.

        Args:
            listing_id: Listing ID

        Returns:
            True if updated, False if not found
        """
        listing = await self.get(listing_id)
        if listing:
            listing.views_count += 1
            await self.db.flush()
            return True
        return False

    async def count_by_seller(self, seller_id: int) -> int:
        """
        Count listings by seller.

        Args:
            seller_id: Seller user ID

        Returns:
            Number of listings by the seller
        """
        result = await self.db.execute(
            select(func.count(Listing.id))
            .where(Listing.seller_id == seller_id)
        )
        return result.scalar_one()


class ListingImageRepository(BaseRepository[ListingImage]):
    """Repository for ListingImage model."""

    def __init__(self, db):
        """
        Initialize listing image repository.

        Args:
            db: Database session
        """
        super().__init__(ListingImage, db)

    async def get_by_listing(
        self,
        listing_id: int
    ) -> List[ListingImage]:
        """
        Get all images for a listing.

        Args:
            listing_id: Listing ID

        Returns:
            List of images ordered by sort_order
        """
        result = await self.db.execute(
            select(ListingImage)
            .where(ListingImage.listing_id == listing_id)
            .order_by(ListingImage.sort_order)
        )
        return list(result.scalars().all())

    async def get_primary_image(
        self,
        listing_id: int
    ) -> ListingImage | None:
        """
        Get primary image for a listing.

        Args:
            listing_id: Listing ID

        Returns:
            Primary image if found, None otherwise
        """
        result = await self.db.execute(
            select(ListingImage)
            .where(
                and_(
                    ListingImage.listing_id == listing_id,
                    ListingImage.is_primary == True
                )
            )
            .order_by(ListingImage.sort_order)
            .limit(1)
        )
        return result.scalar_one_or_none()
