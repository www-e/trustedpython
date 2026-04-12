"""
Content service for managing platform content.

Handles games, categories, promo banners, and FAQ management.
"""

from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.content import Category, FAQItem, Game, PromoBanner
from app.schemas.admin import (
    CategoriesResponse,
    CategoryManagementItem,
    FAQItemResponse,
    FAQResponse,
    GameManagementItem,
    GamesResponse,
    PromoBannerItem,
    PromoBannersResponse,
)


class ContentService:
    """
    Service for managing platform content.

    Provides functionality for managing games, categories,
    promotional banners, and FAQ items.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize ContentService.

        Args:
            db: Async database session
        """
        self.db = db

    async def manage_games(self) -> GamesResponse:
        """
        Get all games for management.

        Returns:
            GamesResponse: List of games
        """
        result = await self.db.execute(select(Game).order_by(desc(Game.is_popular), Game.name))
        games = result.scalars().all()

        game_items = []
        for game in games:
            game_items.append(
                GameManagementItem(
                    id=str(game.id),
                    name=game.name,
                    slug=game.slug,
                    icon_url=game.icon_url,
                    is_active=game.is_active,
                    is_popular=game.is_popular,
                    active_listings=game.active_listings,
                    created_at=game.created_at,
                )
            )

        return GamesResponse(games=game_items)

    async def add_game(
        self, name: str, slug: str, icon_url: Optional[str] = None, is_popular: bool = False
    ) -> Dict[str, Any]:
        """
        Add a new game.

        Args:
            name: Game name
            slug: URL slug
            icon_url: Icon URL
            is_popular: Popular status

        Returns:
            Dict with created game

        Raises:
            ConflictException: If slug already exists
        """
        # Check if slug exists
        existing = await self.db.scalar(select(Game).where(Game.slug == slug))
        if existing:
            raise ConflictException("slug", slug)

        game = Game(name=name, slug=slug, icon_url=icon_url, is_popular=is_popular, is_active=True)
        self.db.add(game)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("add_game", game.id, f"Added game: {name}")

        return {
            "id": str(game.id),
            "name": game.name,
            "slug": game.slug,
            "icon_url": game.icon_url,
            "is_active": game.is_active,
            "is_popular": game.is_popular,
            "active_listings": game.active_listings,
            "created_at": game.created_at,
        }

    async def update_game(
        self,
        game_id: UUID,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        icon_url: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_popular: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update a game.

        Args:
            game_id: Game ID
            name: Game name
            slug: URL slug
            icon_url: Icon URL
            is_active: Active status
            is_popular: Popular status

        Returns:
            Dict with updated game

        Raises:
            NotFoundException: If game not found
            ConflictException: If slug already exists
        """
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()

        if not game:
            raise NotFoundException(str(game_id), "Game")

        # Check if new slug exists
        if slug and slug != game.slug:
            existing = await self.db.scalar(select(Game).where(Game.slug == slug))
            if existing:
                raise ConflictException("slug", slug)

        if name is not None:
            game.name = name
        if slug is not None:
            game.slug = slug
        if icon_url is not None:
            game.icon_url = icon_url
        if is_active is not None:
            game.is_active = is_active
        if is_popular is not None:
            game.is_popular = is_popular

        await self.db.commit()

        # Log admin action
        await self._log_admin_action("update_game", game_id, f"Updated game: {game.name}")

        return {
            "id": str(game.id),
            "name": game.name,
            "slug": game.slug,
            "icon_url": game.icon_url,
            "is_active": game.is_active,
            "is_popular": game.is_popular,
            "active_listings": game.active_listings,
            "created_at": game.created_at,
        }

    async def manage_categories(self) -> CategoriesResponse:
        """
        Get all categories for management.

        Returns:
            CategoriesResponse: List of categories
        """
        result = await self.db.execute(select(Category).order_by(Category.name))
        categories = result.scalars().all()

        category_items = []
        for category in categories:
            category_items.append(
                CategoryManagementItem(
                    id=str(category.id),
                    name=category.name,
                    slug=category.slug,
                    icon=category.icon,
                    description=category.description,
                    is_active=category.is_active,
                    listing_count=category.listing_count,
                )
            )

        return CategoriesResponse(categories=category_items)

    async def add_category(
        self, name: str, slug: str, icon: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new category.

        Args:
            name: Category name
            slug: URL slug
            icon: Icon
            description: Description

        Returns:
            Dict with created category

        Raises:
            ConflictException: If slug already exists
        """
        # Check if slug exists
        existing = await self.db.scalar(select(Category).where(Category.slug == slug))
        if existing:
            raise ConflictException("slug", slug)

        category = Category(
            name=name, slug=slug, icon=icon, description=description, is_active=True
        )
        self.db.add(category)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("add_category", category.id, f"Added category: {name}")

        return {
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
            "icon": category.icon,
            "description": category.description,
            "is_active": category.is_active,
            "listing_count": category.listing_count,
        }

    async def manage_promo_banners(self) -> PromoBannersResponse:
        """
        Get all promo banners.

        Returns:
            PromoBannersResponse: List of promo banners
        """
        result = await self.db.execute(
            select(PromoBanner).order_by(desc(PromoBanner.priority), desc(PromoBanner.created_at))
        )
        banners = result.scalars().all()

        banner_items = []
        for banner in banners:
            banner_items.append(
                PromoBannerItem(
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
                    created_at=banner.created_at,
                )
            )

        return PromoBannersResponse(banners=banner_items)

    async def create_promo_banner(
        self,
        title: str,
        image_url: str,
        subtitle: Optional[str] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        priority: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a new promo banner.

        Args:
            title: Banner title
            image_url: Banner image URL
            subtitle: Banner subtitle
            action_url: Action URL
            action_text: Action button text
            priority: Banner priority
            start_date: Start date
            end_date: End date

        Returns:
            Dict with created banner
        """
        banner = PromoBanner(
            title=title,
            subtitle=subtitle,
            image_url=image_url,
            action_url=action_url,
            action_text=action_text,
            priority=priority,
            start_date=start_date or date.today(),
            end_date=end_date,
            is_active=True,
        )
        self.db.add(banner)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("create_promo_banner", banner.id, f"Created banner: {title}")

        return {
            "id": str(banner.id),
            "title": banner.title,
            "subtitle": banner.subtitle,
            "image_url": banner.image_url,
            "action_url": banner.action_url,
            "action_text": banner.action_text,
            "priority": banner.priority,
            "is_active": banner.is_active,
            "start_date": banner.start_date,
            "end_date": banner.end_date,
            "created_at": banner.created_at,
        }

    async def manage_faq(self) -> FAQResponse:
        """
        Get all FAQ items.

        Returns:
            FAQResponse: List of FAQ items
        """
        result = await self.db.execute(
            select(FAQItem).order_by(FAQItem.category, FAQItem.display_order)
        )
        items = result.scalars().all()

        faq_items = []
        for item in items:
            faq_items.append(
                FAQItemResponse(
                    id=str(item.id),
                    question=item.question,
                    answer=item.answer,
                    category=item.category,
                    display_order=item.display_order,
                    is_active=item.is_active,
                    created_at=item.created_at,
                )
            )

        return FAQResponse(items=faq_items)

    async def add_faq_item(
        self, question: str, answer: str, category: Optional[str] = None, display_order: int = 0
    ) -> Dict[str, Any]:
        """
        Add a new FAQ item.

        Args:
            question: FAQ question
            answer: FAQ answer
            category: FAQ category
            display_order: Display order

        Returns:
            Dict with created FAQ item
        """
        faq_item = FAQItem(
            question=question,
            answer=answer,
            category=category,
            display_order=display_order,
            is_active=True,
        )
        self.db.add(faq_item)
        await self.db.commit()

        # Log admin action
        await self._log_admin_action("add_faq_item", faq_item.id, f"Added FAQ: {question}")

        return {
            "id": str(faq_item.id),
            "question": faq_item.question,
            "answer": faq_item.answer,
            "category": faq_item.category,
            "display_order": faq_item.display_order,
            "is_active": faq_item.is_active,
            "created_at": faq_item.created_at,
        }

    async def _log_admin_action(
        self, action: str, target_id: UUID, notes: Optional[str] = None
    ) -> None:
        """
        Log admin action for audit trail.

        Args:
            action: Action performed
            target_id: ID of target entity
            notes: Optional notes
        """
        # In production, you would save this to an AuditLog model
        # For now, we'll just log it
        logger = __import__("logging").getLogger(__name__)
        logger.info(f"Admin action: {action} on {target_id} - Notes: {notes}")
