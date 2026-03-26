"""Listing image management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import ListingImage
from app.repositories.listing import ListingRepository, ListingImageRepository
from app.schemas.listing import ListingImageCreate
from app.services.listing_auth import ListingAuthService


class ListingImageService:
    """Service for listing image management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize listing image service.

        Args:
            db: Database session
        """
        self.db = db
        self.listing_repo = ListingRepository(db)
        self.image_repo = ListingImageRepository(db)
        self.auth_service = ListingAuthService(db)

    async def add_image(
        self,
        listing_id: int,
        seller_id: int,
        image_data: ListingImageCreate
    ) -> ListingImage:
        """
        Add an image to a listing.

        Args:
            listing_id: Listing ID
            seller_id: Seller user ID (for ownership check)
            image_data: Image data

        Returns:
            Created image

        Raises:
            NotFoundError: If listing not found
            ForbiddenError: If user is not the seller
        """
        # Verify ownership
        await self.auth_service.verify_ownership(listing_id, seller_id)

        # Create image
        image = await self.image_repo.create(
            listing_id=listing_id,
            image_url=image_data.image_url,
            caption=image_data.caption,
            sort_order=image_data.sort_order,
            is_primary=image_data.is_primary
        )

        return image

    async def delete_image(
        self,
        image_id: int,
        seller_id: int
    ) -> bool:
        """
        Delete an image from a listing.

        Args:
            image_id: Image ID
            seller_id: Seller user ID (for ownership check)

        Returns:
            True if deleted

        Raises:
            NotFoundError: If image not found
            ForbiddenError: If user is not the seller
        """
        # Get image
        image = await self.image_repo.get(image_id)
        if not image:
            from app.exceptions import NotFoundError
            raise NotFoundError(f"Image {image_id} not found")

        # Verify ownership of listing
        await self.auth_service.verify_ownership(image.listing_id, seller_id)

        # Delete image
        return await self.image_repo.delete(image_id)

    async def set_primary_image(
        self,
        image_id: int,
        seller_id: int
    ) -> ListingImage:
        """
        Set an image as primary for a listing.

        Args:
            image_id: Image ID
            seller_id: Seller user ID

        Returns:
            Updated image

        Raises:
            NotFoundError: If image not found
            ForbiddenError: If user is not the seller
        """
        # Get image
        image = await self.image_repo.get(image_id)
        if not image:
            from app.exceptions import NotFoundError
            raise NotFoundError(f"Image {image_id} not found")

        # Verify ownership
        await self.auth_service.verify_ownership(image.listing_id, seller_id)

        # Unset current primary
        await self.image_repo.unset_primary_for_listing(image.listing_id)

        # Set new primary
        updated = await self.image_repo.update(image_id, is_primary=True)
        return updated
