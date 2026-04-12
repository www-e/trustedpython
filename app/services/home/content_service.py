"""Content service for home page content management."""

from datetime import date
from typing import List, Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Category, FAQItem, PromoBanner
from app.schemas.home import (
    CategoriesResponse,
    CategoryResponse,
    FAQItemResponse,
    FAQResponse,
    PromoBannerResponse,
    PromoBannersResponse,
)
from app.services.cache_service import CacheService


class ContentService:
    """Service for home page content including categories, banners, and FAQ."""

    def __init__(self, db: AsyncSession, cache_service: Optional[CacheService] = None):
        """
        Initialize ContentService.

        Args:
            db: Async database session
            cache_service: Optional cache service for caching content
        """
        self.db = db
        self.cache = cache_service or CacheService()

    async def get_categories(self) -> CategoriesResponse:
        """
        Get all available categories.

        Returns:
            CategoriesResponse: List of all categories ordered by listing count
        """
        # Try cache first
        cached = await self.cache.get_cached_categories()
        if cached:
            cached_categories = [CategoryResponse(**cat) for cat in cached]
            return CategoriesResponse(categories=cached_categories)

        # Fetch from database
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.listing_count.desc())
        )
        categories: Sequence[Category] = result.scalars().all()

        category_responses: list[CategoryResponse] = []
        for cat in categories:
            category_responses.append(
                CategoryResponse(
                    id=str(cat.id),
                    name=cat.name,
                    slug=cat.slug,
                    icon=cat.icon,
                    description=cat.description,
                    account_count=int(cat.listing_count),
                    is_active=cat.is_active,
                )
            )

        # Cache the results
        categories_dict = [cat.model_dump() for cat in category_responses]
        await self.cache.cache_categories(categories_dict)

        return CategoriesResponse(categories=category_responses)

    async def get_promo_banners(self) -> PromoBannersResponse:
        """
        Get active promotional banners.

        Returns:
            PromoBannersResponse: List of active promo banners ordered by priority
        """
        # Try cache first
        cached = await self.cache.get_cached_promo_banners()
        if cached:
            cached_banners = [PromoBannerResponse(**banner) for banner in cached]
            return PromoBannersResponse(banners=cached_banners)

        # Fetch from database
        today = date.today()

        result = await self.db.execute(
            select(PromoBanner)
            .where(
                and_(
                    PromoBanner.is_active == True,
                    PromoBanner.start_date <= today,
                    or_(PromoBanner.end_date.is_(None), PromoBanner.end_date >= today),
                )
            )
            .order_by(PromoBanner.priority.desc(), PromoBanner.created_at.desc())
        )
        banners: Sequence[PromoBanner] = result.scalars().all()

        banner_responses: list[PromoBannerResponse] = []
        for banner in banners:
            banner_responses.append(
                PromoBannerResponse(
                    id=str(banner.id),
                    title=banner.title,
                    subtitle=banner.subtitle,
                    image_url=banner.image_url,
                    action_url=banner.action_url,
                    action_text=banner.action_text,
                    priority=banner.priority,
                    is_active=banner.is_active,
                    start_date=banner.start_date,
                    end_date=banner.end_date,
                )
            )

        # Cache the results
        banners_dict = [banner.model_dump() for banner in banner_responses]
        await self.cache.cache_promo_banners(banners_dict)

        return PromoBannersResponse(banners=banner_responses)

    async def get_faq(self) -> FAQResponse:
        """
        Get FAQ items.

        Returns:
            FAQResponse: List of FAQ items ordered by display order
        """
        # Try cache first
        cached = await self.cache.get_cached_faq()
        if cached:
            cached_faq_items = [FAQItemResponse(**item) for item in cached]
            return FAQResponse(faq_items=cached_faq_items)

        # Fetch from database
        result = await self.db.execute(
            select(FAQItem)
            .where(FAQItem.is_active == True)
            .order_by(FAQItem.display_order.asc(), FAQItem.created_at.asc())
        )
        faq_items: Sequence[FAQItem] = result.scalars().all()

        faq_responses: list[FAQItemResponse] = []
        for item in faq_items:
            faq_responses.append(
                FAQItemResponse(
                    id=str(item.id),
                    question=item.question,
                    answer=item.answer,
                    category=item.category,
                    order=item.display_order,
                )
            )

        # Cache the results
        faq_dict = [item.model_dump() for item in faq_responses]
        await self.cache.cache_faq(faq_dict)

        return FAQResponse(faq_items=faq_responses)
