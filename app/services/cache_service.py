"""Redis caching service for home feed data."""

import json
from datetime import timedelta
from typing import Any, List, Optional, cast

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis


class CacheService:
    """Service for caching frequently accessed home feed data."""

    # Cache TTL constants
    FEATURED_ACCOUNTS_TTL = timedelta(hours=6)
    CATEGORIES_TTL = timedelta(hours=24)
    GAMES_TTL = timedelta(hours=24)
    PROMO_BANNERS_TTL = timedelta(hours=1)
    FAQ_TTL = timedelta(hours=24)

    # Cache key prefixes
    FEATURED_ACCOUNTS_KEY = "home:featured:accounts"
    CATEGORIES_KEY = "home:categories"
    GAMES_KEY = "home:games"
    PROMO_BANNERS_KEY = "home:promo:banners"
    FAQ_KEY = "home:faq"

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client

    async def _get_redis(self) -> Optional[Redis]:
        """Get Redis client."""
        if self.redis_client:
            return self.redis_client
        return await get_redis()

    async def get_cached_featured_accounts(self) -> Optional[List[dict]]:
        """
        Get cached featured accounts.

        Returns:
            List of account dicts or None if not cached
        """
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            cached = await redis.get(self.FEATURED_ACCOUNTS_KEY)
            if cached:
                return cast(List[dict], json.loads(cached))
        except Exception:
            # Fail silently - return None to fetch from DB
            pass

        return None

    async def cache_featured_accounts(self, accounts: List[dict]) -> None:
        """
        Cache featured accounts.

        Args:
            accounts: List of account dicts to cache
        """
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.setex(
                self.FEATURED_ACCOUNTS_KEY,
                int(self.FEATURED_ACCOUNTS_TTL.total_seconds()),
                json.dumps(accounts),
            )
        except Exception:
            # Fail silently - cache miss is acceptable
            pass

    async def invalidate_featured_accounts(self) -> None:
        """Invalidate featured accounts cache."""
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.delete(self.FEATURED_ACCOUNTS_KEY)
        except Exception:
            pass

    async def get_cached_categories(self) -> list[dict[Any, Any]] | None:
        """
        Get cached categories.

        Returns:
            List of category dicts or None if not cached
        """
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            cached = await redis.get(self.CATEGORIES_KEY)
            if cached:
                result: list[dict[Any, Any]] = json.loads(cached)
                return result
        except Exception:
            pass

        return None

    async def cache_categories(self, categories: List[dict]) -> None:
        """
        Cache categories.

        Args:
            categories: List of category dicts to cache
        """
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.setex(
                self.CATEGORIES_KEY,
                int(self.CATEGORIES_TTL.total_seconds()),
                json.dumps(categories),
            )
        except Exception:
            pass

    async def invalidate_categories(self) -> None:
        """Invalidate categories cache."""
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.delete(self.CATEGORIES_KEY)
        except Exception:
            pass

    async def get_cached_games(self, sort: str = "name") -> Optional[List[dict]]:
        """
        Get cached games.

        Args:
            sort: Sort order used for caching

        Returns:
            List of game dicts or None if not cached
        """
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            key = f"{self.GAMES_KEY}:{sort}"
            cached = await redis.get(key)
            if cached:
                result: list[dict[Any, Any]] = json.loads(cached)
                return result
        except Exception:
            pass

        return None

    async def cache_games(self, games: List[dict], sort: str = "name") -> None:
        """
        Cache games.

        Args:
            games: List of game dicts to cache
            sort: Sort order for cache key
        """
        redis = await self._get_redis()
        if not redis:
            return

        try:
            key = f"{self.GAMES_KEY}:{sort}"
            await redis.setex(key, int(self.GAMES_TTL.total_seconds()), json.dumps(games))
        except Exception:
            pass

    async def invalidate_games(self) -> None:
        """Invalidate all games caches."""
        redis = await self._get_redis()
        if not redis:
            return

        try:
            # Delete all game cache keys
            pattern = f"{self.GAMES_KEY}:*"
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
        except Exception:
            pass

    async def get_cached_promo_banners(self) -> list[dict[Any, Any]] | None:
        """
        Get cached promotional banners.

        Returns:
            List of banner dicts or None if not cached
        """
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            cached = await redis.get(self.PROMO_BANNERS_KEY)
            if cached:
                result: list[dict[Any, Any]] = json.loads(cached)
                return result
        except Exception:
            pass

        return None

    async def cache_promo_banners(self, banners: List[dict]) -> None:
        """
        Cache promotional banners.

        Args:
            banners: List of banner dicts to cache
        """
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.setex(
                self.PROMO_BANNERS_KEY,
                int(self.PROMO_BANNERS_TTL.total_seconds()),
                json.dumps(banners),
            )
        except Exception:
            pass

    async def invalidate_promo_banners(self) -> None:
        """Invalidate promo banners cache."""
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.delete(self.PROMO_BANNERS_KEY)
        except Exception:
            pass

    async def get_cached_faq(self) -> list[dict[Any, Any]] | None:
        """
        Get cached FAQ items.

        Returns:
            List of FAQ dicts or None if not cached
        """
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            cached = await redis.get(self.FAQ_KEY)
            if cached:
                result: list[dict[Any, Any]] = json.loads(cached)
                return result
        except Exception:
            pass

        return None

    async def cache_faq(self, faq_items: List[dict]) -> None:
        """
        Cache FAQ items.

        Args:
            faq_items: List of FAQ dicts to cache
        """
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.setex(
                self.FAQ_KEY, int(self.FAQ_TTL.total_seconds()), json.dumps(faq_items)
            )
        except Exception:
            pass

    async def invalidate_faq(self) -> None:
        """Invalidate FAQ cache."""
        redis = await self._get_redis()
        if not redis:
            return

        try:
            await redis.delete(self.FAQ_KEY)
        except Exception:
            pass

    async def invalidate_all_home_cache(self) -> None:
        """Invalidate all home feed caches."""
        await self.invalidate_featured_accounts()
        await self.invalidate_categories()
        await self.invalidate_games()
        await self.invalidate_promo_banners()
        await self.invalidate_faq()
