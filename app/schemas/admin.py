"""
Admin Dashboard schemas for platform management.
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Dashboard Stats & Analytics
# ============================================================================


class DashboardStatsResponse(BaseModel):
    """Dashboard overview statistics."""

    users: dict = Field(
        ..., description="User statistics (total, active_today, new_this_week, verified, suspended)"
    )
    listings: dict = Field(
        ..., description="Listing statistics (total, active, pending_approval, sold_this_week)"
    )
    deals: dict = Field(
        ...,
        description="Deal statistics (total, active, completed_this_week, disputed, success_rate)",
    )
    mediators: dict = Field(
        ..., description="Mediator statistics (total, active, verified, avg_response_time)"
    )
    revenue: dict = Field(
        ..., description="Revenue statistics (this_month, last_month, growth_percentage)"
    )


class UserGrowthData(BaseModel):
    """User growth data point."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    new_users: int = Field(..., description="Number of new users")
    active_users: int = Field(..., description="Number of active users")


class DealVolumeData(BaseModel):
    """Deal volume data point."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    deals: int = Field(..., description="Number of deals")
    completed: int = Field(..., description="Number of completed deals")


class TopGameData(BaseModel):
    """Top game data."""

    game: str = Field(..., description="Game name")
    listings: int = Field(..., description="Number of listings")
    deals: int = Field(..., description="Number of deals")


class TopMediatorData(BaseModel):
    """Top mediator data."""

    id: str = Field(..., description="Mediator ID")
    name: str = Field(..., description="Mediator name")
    deals_completed: int = Field(..., description="Number of completed deals")
    avg_rating: float = Field(..., description="Average rating")


class RevenueTrendData(BaseModel):
    """Revenue trend data point."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    amount: float = Field(..., description="Revenue amount")


class AnalyticsResponse(BaseModel):
    """Detailed analytics response."""

    user_growth: List[UserGrowthData] = Field(..., description="User growth over time")
    deal_volume: List[DealVolumeData] = Field(..., description="Deal volume over time")
    top_games: List[TopGameData] = Field(..., description="Top performing games")
    top_mediators: List[TopMediatorData] = Field(..., description="Top performing mediators")
    revenue_trend: List[RevenueTrendData] = Field(..., description="Revenue trend over time")


# ============================================================================
# User Management
# ============================================================================


class UserStatsInList(BaseModel):
    """User stats in list view."""

    total_deals: int = Field(..., description="Total deals")
    rating: float = Field(..., description="Average rating")
    listings_count: int = Field(..., description="Number of listings")


class UserListItem(BaseModel):
    """User in list view."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_verified: bool = Field(..., description="Verification status")
    is_suspended: bool = Field(..., description="Suspension status")
    is_banned: bool = Field(default=False, description="Ban status")
    role: str = Field(..., description="User role (user, mediator, admin)")
    stats: UserStatsInList = Field(..., description="User statistics")
    created_at: datetime = Field(..., description="Account creation date")
    last_login_at: Optional[datetime] = Field(None, description="Last login date")


class UserListResponse(BaseModel):
    """User list response."""

    users: List[UserListItem] = Field(..., description="List of users")
    pagination: dict = Field(..., description="Pagination information")


class UserProfileInDetail(BaseModel):
    """User profile in detail view."""

    bio: Optional[str] = Field(None, description="User bio")
    user_role: str = Field(..., description="User role")
    member_since: Optional[date] = Field(None, description="Member since date")
    completed_deals: int = Field(..., description="Completed deals count")
    rating: float = Field(..., description="Average rating")
    accounts_sold: int = Field(..., description="Accounts sold count")
    bought_count: int = Field(..., description="Accounts bought count")


class LoginHistoryItem(BaseModel):
    """Login history entry."""

    timestamp: datetime = Field(..., description="Login timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    device_info: Optional[str] = Field(None, description="Device information")
    status: str = Field(..., description="Login status (success, failed)")


class UserDetailResponse(BaseModel):
    """User detail response."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_verified: bool = Field(..., description="Verification status")
    is_email_verified: bool = Field(..., description="Email verification status")
    is_suspended: bool = Field(..., description="Suspension status")
    suspension_reason: Optional[str] = Field(None, description="Suspension reason")
    is_banned: bool = Field(default=False, description="Ban status")
    ban_reason: Optional[str] = Field(None, description="Ban reason")
    profile: UserProfileInDetail = Field(..., description="User profile")
    listings: int = Field(..., description="Number of listings")
    active_deals: int = Field(..., description="Number of active deals")
    reports_against: int = Field(..., description="Number of reports against user")
    login_history: List[LoginHistoryItem] = Field(..., description="Login history")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")


class VerifyUserRequest(BaseModel):
    """Request to verify a user."""

    notes: Optional[str] = Field(None, description="Admin notes")


class SuspendUserRequest(BaseModel):
    """Request to suspend a user."""

    reason: str = Field(..., min_length=5, description="Suspension reason")
    duration_days: Optional[int] = Field(
        None, ge=1, description="Duration in days (null = indefinite)"
    )


class BanUserRequest(BaseModel):
    """Request to ban a user."""

    reason: str = Field(..., min_length=5, description="Ban reason")


# ============================================================================
# Listing Moderation
# ============================================================================


class SellerInListing(BaseModel):
    """Seller info in listing."""

    id: str = Field(..., description="Seller ID")
    username: str = Field(..., description="Seller username")
    is_verified: bool = Field(..., description="Seller verification status")


class ListingInModeration(BaseModel):
    """Listing in moderation queue."""

    id: str = Field(..., description="Listing ID")
    title: str = Field(..., description="Listing title")
    price: float = Field(..., description="Listing price")
    game: Optional[str] = Field(None, description="Game name")
    seller: SellerInListing = Field(..., description="Seller information")
    status: str = Field(..., description="Listing status")
    image_urls: List[str] = Field(default_factory=list, description="Listing image URLs")
    created_at: datetime = Field(..., description="Creation date")
    waiting_hours: float = Field(..., description="Hours waiting for approval")


class ListingModerationResponse(BaseModel):
    """Pending listings response."""

    listings: List[ListingInModeration] = Field(..., description="Pending listings")
    pagination: dict = Field(..., description="Pagination information")


class ApproveListingRequest(BaseModel):
    """Request to approve a listing."""

    notes: Optional[str] = Field(None, description="Admin notes")


class RejectListingRequest(BaseModel):
    """Request to reject a listing."""

    reason: str = Field(..., min_length=5, description="Rejection reason")


# ============================================================================
# Deal Management
# ============================================================================


class DealInAdminList(BaseModel):
    """Deal in admin list view."""

    id: str = Field(..., description="Deal ID")
    status: str = Field(..., description="Deal status")
    account_title: str = Field(..., description="Account/listing title")
    price: float = Field(..., description="Deal price")
    buyer_username: str = Field(..., description="Buyer username")
    seller_username: str = Field(..., description="Seller username")
    mediator_name: Optional[str] = Field(None, description="Mediator name")
    created_at: datetime = Field(..., description="Deal creation date")
    is_disputed: bool = Field(default=False, description="Whether deal is disputed")


class DealListResponse(BaseModel):
    """Deal list response."""

    deals: List[DealInAdminList] = Field(..., description="List of deals")
    pagination: dict = Field(..., description="Pagination information")


class DealDetailForAdmin(BaseModel):
    """Deal detail for admin view."""

    id: str = Field(..., description="Deal ID")
    status: str = Field(..., description="Deal status")
    account_id: Optional[str] = Field(None, description="Account ID")
    listing_id: Optional[str] = Field(None, description="Listing ID")
    account_title: str = Field(..., description="Account/listing title")
    game: Optional[str] = Field(None, description="Game name")
    price: float = Field(..., description="Deal price")
    buyer: dict = Field(..., description="Buyer information")
    seller: dict = Field(..., description="Seller information")
    mediator: Optional[dict] = Field(None, description="Mediator information")
    payment_status: Optional[str] = Field(None, description="Payment status")
    payment_screenshot: Optional[str] = Field(None, description="Payment screenshot URL")
    chat_room_id: Optional[str] = Field(None, description="Chat room ID")
    notes: Optional[str] = Field(None, description="Deal notes")
    dispute_reason: Optional[str] = Field(None, description="Dispute reason")
    created_at: datetime = Field(..., description="Deal creation date")
    updated_at: datetime = Field(..., description="Last update date")
    completed_at: Optional[datetime] = Field(None, description="Completion date")


class ResolveDisputeRequest(BaseModel):
    """Request to resolve a dispute."""

    decision: str = Field(
        ..., pattern="^(buyer|seller|refund)$", description="Dispute resolution decision"
    )
    resolution_notes: str = Field(..., min_length=10, description="Resolution notes")
    refund_amount: Optional[float] = Field(None, ge=0, description="Refund amount if applicable")


class CancelDealRequest(BaseModel):
    """Request to cancel a deal."""

    reason: str = Field(..., min_length=5, description="Cancellation reason")


# ============================================================================
# Mediator Management
# ============================================================================


class MediatorInAdminList(BaseModel):
    """Mediator in admin list view."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_verified: bool = Field(..., description="Verification status")
    tier: Optional[str] = Field(None, description="Mediator tier")
    deals_completed: int = Field(..., description="Completed deals count")
    avg_rating: float = Field(..., description="Average rating")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Account creation date")


class MediatorListResponse(BaseModel):
    """Mediator list response."""

    mediators: List[MediatorInAdminList] = Field(..., description="List of mediators")
    pagination: dict = Field(..., description="Pagination information")


class MediatorDetailForAdmin(BaseModel):
    """Mediator detail for admin view."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    is_verified: bool = Field(..., description="Verification status")
    tier: Optional[str] = Field(None, description="Mediator tier")
    specialization: Optional[str] = Field(None, description="Specialization")
    experience: Optional[str] = Field(None, description="Experience level")
    bio: Optional[str] = Field(None, description="Bio")
    deals_completed: int = Field(..., description="Completed deals count")
    avg_rating: float = Field(..., description="Average rating")
    response_rate: Optional[float] = Field(None, description="Response rate percentage")
    avg_response_time: Optional[int] = Field(None, description="Average response time in minutes")
    payment_methods: List[dict] = Field(
        default_factory=list, description="Accepted payment methods"
    )
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Account creation date")
    verified_at: Optional[datetime] = Field(None, description="Verification date")


class UpdateMediatorTierRequest(BaseModel):
    """Request to update mediator tier."""

    tier: str = Field(..., pattern="^(bronze|silver|gold|elite)$", description="New tier")
    reason: Optional[str] = Field(None, description="Reason for tier change")


# ============================================================================
# Mediator Applications
# ============================================================================


class ApplicationPaymentMethod(BaseModel):
    """Payment method in application."""

    type: str = Field(..., description="Payment method type")
    name: str = Field(..., description="Payment method name")


class UserInApplication(BaseModel):
    """User info in application."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class MediatorApplicationItem(BaseModel):
    """Mediator application item."""

    id: str = Field(..., description="Application ID")
    user: UserInApplication = Field(..., description="User information")
    specialization: Optional[str] = Field(None, description="Specialization")
    experience: Optional[str] = Field(None, description="Experience level")
    payment_methods: List[ApplicationPaymentMethod] = Field(
        default_factory=list, description="Payment methods"
    )
    bio: Optional[str] = Field(None, description="Bio")
    status: str = Field(..., description="Application status")
    applied_at: datetime = Field(..., description="Application date")


class MediatorApplicationsResponse(BaseModel):
    """Mediator applications response."""

    applications: List[MediatorApplicationItem] = Field(..., description="List of applications")
    pagination: dict = Field(..., description="Pagination information")


class RejectApplicationRequest(BaseModel):
    """Request to reject application."""

    reason: str = Field(..., min_length=5, description="Rejection reason")


# ============================================================================
# Reports & Moderation
# ============================================================================


class ReporterInfo(BaseModel):
    """Reporter information."""

    id: str = Field(..., description="Reporter ID")
    username: str = Field(..., description="Reporter username")


class ReportedUserInfo(BaseModel):
    """Reported user information."""

    id: str = Field(..., description="Reported user ID")
    username: str = Field(..., description="Reported username")


class ReportItem(BaseModel):
    """Report item."""

    id: str = Field(..., description="Report ID")
    reporter: ReporterInfo = Field(..., description="Reporter information")
    reported_user: Optional[ReportedUserInfo] = Field(None, description="Reported user")
    type: str = Field(..., description="Report type (user, listing, message, deal)")
    target_id: Optional[str] = Field(None, description="ID of reported item")
    reason: str = Field(..., description="Report reason")
    description: Optional[str] = Field(None, description="Report description")
    status: str = Field(..., description="Report status (pending, resolved, dismissed)")
    created_at: datetime = Field(..., description="Report creation date")


class ReportsResponse(BaseModel):
    """Reports response."""

    reports: List[ReportItem] = Field(..., description="List of reports")
    pagination: dict = Field(..., description="Pagination information")


class ReportDetailForAdmin(BaseModel):
    """Report detail for admin view."""

    id: str = Field(..., description="Report ID")
    reporter: dict = Field(..., description="Reporter information")
    reported_user: Optional[dict] = Field(None, description="Reported user information")
    type: str = Field(..., description="Report type")
    target_id: Optional[str] = Field(None, description="ID of reported item")
    target_details: Optional[dict] = Field(None, description="Details of reported item")
    reason: str = Field(..., description="Report reason")
    description: Optional[str] = Field(None, description="Report description")
    status: str = Field(..., description="Report status")
    admin_notes: Optional[str] = Field(None, description="Admin notes")
    resolved_at: Optional[datetime] = Field(None, description="Resolution date")
    resolved_by: Optional[str] = Field(None, description="Admin who resolved")
    created_at: datetime = Field(..., description="Report creation date")


class ResolveReportRequest(BaseModel):
    """Request to resolve a report."""

    action: str = Field(
        ..., pattern="^(none|warning|suspend|ban|remove_content)$", description="Action taken"
    )
    notes: str = Field(..., min_length=5, description="Resolution notes")


class BlockedUserItem(BaseModel):
    """Blocked user item."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    block_reason: str = Field(..., description="Block reason")
    blocked_at: datetime = Field(..., description="Block date")
    block_type: str = Field(..., description="Block type (suspended, banned)")


class BlockedUsersResponse(BaseModel):
    """Blocked users response."""

    users: List[BlockedUserItem] = Field(..., description="List of blocked users")
    pagination: dict = Field(..., description="Pagination information")


# ============================================================================
# Platform Configuration
# ============================================================================


class GameManagementItem(BaseModel):
    """Game in management view."""

    id: str = Field(..., description="Game ID")
    name: str = Field(..., description="Game name")
    slug: str = Field(..., description="URL slug")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    is_active: bool = Field(..., description="Active status")
    is_popular: bool = Field(..., description="Popular status")
    active_listings: int = Field(..., description="Active listings count")
    created_at: datetime = Field(..., description="Creation date")


class GamesResponse(BaseModel):
    """Games response."""

    games: List[GameManagementItem] = Field(..., description="List of games")


class AddGameRequest(BaseModel):
    """Request to add a game."""

    name: str = Field(..., min_length=2, max_length=100, description="Game name")
    slug: str = Field(..., min_length=2, max_length=100, description="URL slug")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    is_popular: bool = Field(default=False, description="Popular status")


class UpdateGameRequest(BaseModel):
    """Request to update a game."""

    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Game name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, description="URL slug")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_popular: Optional[bool] = Field(None, description="Popular status")


class CategoryManagementItem(BaseModel):
    """Category in management view."""

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL slug")
    icon: Optional[str] = Field(None, description="Icon")
    description: Optional[str] = Field(None, description="Description")
    is_active: bool = Field(..., description="Active status")
    listing_count: int = Field(..., description="Listing count")


class CategoriesResponse(BaseModel):
    """Categories response."""

    categories: List[CategoryManagementItem] = Field(..., description="List of categories")


class AddCategoryRequest(BaseModel):
    """Request to add a category."""

    name: str = Field(..., min_length=2, max_length=100, description="Category name")
    slug: str = Field(..., min_length=2, max_length=100, description="URL slug")
    icon: Optional[str] = Field(None, description="Icon")
    description: Optional[str] = Field(None, description="Description")


class UpdateCategoryRequest(BaseModel):
    """Request to update a category."""

    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Category name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, description="URL slug")
    icon: Optional[str] = Field(None, description="Icon")
    description: Optional[str] = Field(None, description="Description")
    is_active: Optional[bool] = Field(None, description="Active status")


class PromoBannerItem(BaseModel):
    """Promo banner item."""

    id: str = Field(..., description="Banner ID")
    title: str = Field(..., description="Banner title")
    subtitle: Optional[str] = Field(None, description="Banner subtitle")
    image_url: str = Field(..., description="Banner image URL")
    action_url: Optional[str] = Field(None, description="Action URL")
    action_text: Optional[str] = Field(None, description="Action button text")
    priority: int = Field(..., description="Banner priority")
    is_active: bool = Field(..., description="Active status")
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    created_at: datetime = Field(..., description="Creation date")


class PromoBannersResponse(BaseModel):
    """Promo banners response."""

    banners: List[PromoBannerItem] = Field(..., description="List of banners")


class CreatePromoBannerRequest(BaseModel):
    """Request to create promo banner."""

    title: str = Field(..., min_length=3, max_length=200, description="Banner title")
    subtitle: Optional[str] = Field(None, max_length=300, description="Banner subtitle")
    image_url: str = Field(..., description="Banner image URL")
    action_url: Optional[str] = Field(None, description="Action URL")
    action_text: Optional[str] = Field(None, max_length=100, description="Action button text")
    priority: int = Field(default=0, description="Banner priority")
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="End date")


class FAQItemResponse(BaseModel):
    """FAQ item response."""

    id: str = Field(..., description="FAQ ID")
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")
    category: Optional[str] = Field(None, description="FAQ category")
    display_order: int = Field(..., description="Display order")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation date")


class FAQResponse(BaseModel):
    """FAQ response."""

    items: List[FAQItemResponse] = Field(..., description="List of FAQ items")


class AddFAQItemRequest(BaseModel):
    """Request to add FAQ item."""

    question: str = Field(..., min_length=5, max_length=300, description="FAQ question")
    answer: str = Field(..., min_length=10, description="FAQ answer")
    category: Optional[str] = Field(None, max_length=100, description="FAQ category")
    display_order: int = Field(default=0, description="Display order")
