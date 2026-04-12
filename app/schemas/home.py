"""Home feed schemas for the main discovery interface."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AccountTier(str, Enum):
    """Account tier levels."""

    GOLD = "gold"
    ELITE = "elite"


class AccountCard(BaseModel):
    """Account card for home feed and browse views."""

    id: str = Field(..., description="Account ID")
    title: str = Field(..., description="Account title")
    game: str = Field(..., description="Game name")
    price: float = Field(..., ge=0, description="Account price")
    currency: str = Field("EGP", description="Currency code")
    image_url: str = Field(..., description="Main account image URL")
    rating: float = Field(..., ge=0, le=5, description="Account rating (0-5)")
    reviews: int = Field(..., ge=0, description="Number of reviews")
    is_premium: bool = Field(False, description="Whether this is a premium listing")
    tier: Optional[AccountTier] = Field(None, description="Account tier (gold/elite)")
    seller_name: Optional[str] = Field(None, description="Seller username")
    rank: Optional[str] = Field(None, description="Account rank/level")

    model_config = {"from_attributes": True}


class FeaturedAccountCard(AccountCard):
    """Featured account with seller info."""

    tier: AccountTier = Field(..., description="Account tier (gold/elite)")
    seller: Optional["FeaturedSellerInfo"] = Field(None, description="Seller information")


class FeaturedSellerInfo(BaseModel):
    """Minimal seller info for featured accounts."""

    username: str = Field(..., description="Seller username")
    avatar_url: Optional[str] = Field(None, description="Seller avatar URL")
    rating: float = Field(..., ge=0, le=5, description="Seller rating")


class CategoryItem(BaseModel):
    """Category item for home feed."""

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    icon: Optional[str] = Field(None, description="Category icon identifier")
    count: int = Field(..., ge=0, description="Number of accounts in category")

    model_config = {"from_attributes": True}


class HomeFeedData(BaseModel):
    """Home feed main data structure."""

    featured_accounts: List[FeaturedAccountCard] = Field(
        default_factory=list, description="Featured/premium accounts"
    )
    accounts: List[AccountCard] = Field(
        default_factory=list, description="Regular account listings"
    )
    categories: List[CategoryItem] = Field(default_factory=list, description="Available categories")


class HomeFeedResponse(BaseModel):
    """Complete home feed response."""

    featured_accounts: List[FeaturedAccountCard] = Field(
        default_factory=list, description="Featured/premium accounts"
    )
    accounts: List[AccountCard] = Field(
        default_factory=list, description="Regular account listings"
    )
    categories: List[CategoryItem] = Field(default_factory=list, description="Available categories")
    pagination: dict = Field(..., description="Pagination information")


class FeaturedAccountsData(BaseModel):
    """Featured accounts response data."""

    accounts: List[FeaturedAccountCard] = Field(..., description="List of featured accounts")


class FeaturedAccountsResponse(BaseModel):
    """Featured accounts response."""

    accounts: List[FeaturedAccountCard] = Field(..., description="List of featured accounts")


class CategoryResponse(BaseModel):
    """Full category response."""

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly slug")
    icon: Optional[str] = Field(None, description="Icon identifier")
    description: Optional[str] = Field(None, description="Category description")
    account_count: int = Field(..., ge=0, description="Number of accounts")
    is_active: bool = Field(..., description="Whether category is active")

    model_config = {"from_attributes": True}


class CategoriesData(BaseModel):
    """Categories response data."""

    categories: List[CategoryResponse] = Field(..., description="List of categories")


class CategoriesResponse(BaseModel):
    """Categories list response."""

    categories: List[CategoryResponse] = Field(..., description="List of categories")


class PromoBannerResponse(BaseModel):
    """Promotional banner response."""

    id: str = Field(..., description="Banner ID")
    title: str = Field(..., description="Banner title")
    subtitle: Optional[str] = Field(None, description="Banner subtitle")
    image_url: str = Field(..., description="Banner image URL")
    action_url: Optional[str] = Field(None, description="Action link URL")
    action_text: Optional[str] = Field(None, description="Action button text")
    priority: int = Field(..., ge=0, description="Display priority (higher first)")
    is_active: bool = Field(..., description="Whether banner is active")
    start_date: date = Field(..., description="Campaign start date")
    end_date: Optional[date] = Field(None, description="Campaign end date")

    model_config = {"from_attributes": True}


class PromoBannersData(BaseModel):
    """Promo banners response data."""

    banners: List[PromoBannerResponse] = Field(..., description="List of promotional banners")


class PromoBannersResponse(BaseModel):
    """Promotional banners response."""

    banners: List[PromoBannerResponse] = Field(..., description="List of promotional banners")


class FAQItemResponse(BaseModel):
    """FAQ item response."""

    id: str = Field(..., description="FAQ item ID")
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")
    category: Optional[str] = Field(None, description="FAQ category")
    order: int = Field(..., ge=0, description="Display order")

    model_config = {"from_attributes": True}


class FAQData(BaseModel):
    """FAQ response data."""

    faq_items: List[FAQItemResponse] = Field(..., description="List of FAQ items")


class FAQResponse(BaseModel):
    """FAQ response."""

    faq_items: List[FAQItemResponse] = Field(..., description="List of FAQ items")


class SearchAccountCard(AccountCard):
    """Account card for search results with highlights."""

    highlights: List[str] = Field(default_factory=list, description="Matched text snippets")


class SearchFilters(BaseModel):
    """Available search filters."""

    available_games: List[str] = Field(
        default_factory=list, description="Available games to filter by"
    )
    price_range: dict = Field(default_factory=dict, description="Available price range {min, max}")


class SearchData(BaseModel):
    """Search response data."""

    query: str = Field(..., description="Search query")
    total_results: int = Field(..., ge=0, description="Total matching results")
    accounts: List[SearchAccountCard] = Field(..., description="Search results")
    filters: SearchFilters = Field(..., description="Available filters")
    pagination: dict = Field(..., description="Pagination information")


class SearchResponse(BaseModel):
    """Search response."""

    query: str = Field(..., description="Search query")
    total_results: int = Field(..., ge=0, description="Total matching results")
    accounts: List[SearchAccountCard] = Field(..., description="Search results")
    filters: SearchFilters = Field(..., description="Available filters")
    pagination: dict = Field(..., description="Pagination information")


class GameResponse(BaseModel):
    """Game response."""

    id: str = Field(..., description="Game ID")
    name: str = Field(..., description="Game name")
    slug: str = Field(..., description="URL-friendly slug")
    icon_url: Optional[str] = Field(None, description="Game icon URL")
    banner_url: Optional[str] = Field(None, description="Game banner URL")
    description: Optional[str] = Field(None, description="Game description")
    active_listings: int = Field(..., ge=0, description="Number of active listings")
    avg_price: Optional[float] = Field(None, description="Average listing price")
    is_popular: bool = Field(..., description="Whether game is popular")
    is_trending: bool = Field(..., description="Whether game is trending")

    model_config = {"from_attributes": True}


class GamesData(BaseModel):
    """Games response data."""

    games: List[GameResponse] = Field(..., description="List of games")


class GamesResponse(BaseModel):
    """Games list response."""

    games: List[GameResponse] = Field(..., description="List of games")


class GameInfo(BaseModel):
    """Basic game info."""

    id: str = Field(..., description="Game ID")
    name: str = Field(..., description="Game name")
    icon_url: Optional[str] = Field(None, description="Game icon URL")


class GameAccountSeller(BaseModel):
    """Seller info for game accounts."""

    username: str = Field(..., description="Seller username")
    avatar_url: Optional[str] = Field(None, description="Seller avatar URL")


class GameAccountCard(AccountCard):
    """Account card for game listings with seller info."""

    seller: Optional[GameAccountSeller] = Field(None, description="Seller information")


class GameAccountsData(BaseModel):
    """Game accounts response data."""

    game: GameInfo = Field(..., description="Game information")
    accounts: List[GameAccountCard] = Field(..., description="Accounts for this game")
    pagination: dict = Field(..., description="Pagination information")


class GameAccountsResponse(BaseModel):
    """Game accounts response."""

    game: GameInfo = Field(..., description="Game information")
    accounts: List[GameAccountCard] = Field(..., description="Accounts for this game")
    pagination: dict = Field(..., description="Pagination information")
