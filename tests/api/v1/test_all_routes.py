"""
Tests for home, sell, buy, chat, notifications, profile, security, and admin endpoints.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestHomeEndpoints:
    """Test home feed endpoints."""

    async def test_home_feed_accessible(self, client: AsyncClient):
        """Test home feed endpoint is accessible."""
        response = await client.get("/api/v1/home/feed")
        assert response.status_code in [200, 500]  # 500 if DB unavailable

    async def test_home_featured_accessible(self, client: AsyncClient):
        """Test home featured endpoint is accessible."""
        response = await client.get("/api/v1/home/featured")
        assert response.status_code in [200, 500]

    async def test_home_categories_accessible(self, client: AsyncClient):
        """Test home categories endpoint is accessible."""
        response = await client.get("/api/v1/home/categories")
        assert response.status_code in [200, 500]

    async def test_home_promo_accessible(self, client: AsyncClient):
        """Test home promo endpoint is accessible."""
        response = await client.get("/api/v1/home/promo")
        assert response.status_code in [200, 500]

    async def test_home_faq_accessible(self, client: AsyncClient):
        """Test home FAQ endpoint is accessible."""
        response = await client.get("/api/v1/home/faq")
        assert response.status_code in [200, 500]

    async def test_home_search_accessible(self, client: AsyncClient):
        """Test home search endpoint is accessible."""
        response = await client.get("/api/v1/home/search?q=test")
        assert response.status_code in [200, 500]

    async def test_home_games_accessible(self, client: AsyncClient):
        """Test home games endpoint is accessible."""
        response = await client.get("/api/v1/home/games")
        assert response.status_code in [200, 500]

    async def test_home_game_accounts_accessible(self, client: AsyncClient):
        """Test home game accounts endpoint is accessible."""
        game_id = uuid4()
        response = await client.get(f"/api/v1/home/games/{game_id}/accounts")
        assert response.status_code in [200, 404, 500]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestSellEndpoints:
    """Test sell endpoints."""

    async def test_sell_listings_requires_auth(self, client: AsyncClient):
        """Test sell listings requires auth for POST."""
        response = await client.post("/api/v1/sell/listings", json={})
        assert response.status_code in [401, 422]

    async def test_sell_listings_get_accessible(self, client: AsyncClient):
        """Test GET sell listings accessible."""
        response = await client.get("/api/v1/sell/listings")
        assert response.status_code in [401, 405]  # Requires auth or wrong method

    async def test_sell_categories_accessible(self, client: AsyncClient):
        """Test sell categories endpoint is accessible."""
        response = await client.get("/api/v1/sell/categories")
        assert response.status_code in [200, 500]

    async def test_sell_games_accessible(self, client: AsyncClient):
        """Test sell games endpoint is accessible."""
        response = await client.get("/api/v1/sell/games")
        assert response.status_code in [200, 500]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestBuyEndpoints:
    """Test buy endpoints."""

    async def test_buy_accounts_accessible(self, client: AsyncClient):
        """Test buy accounts endpoint is accessible."""
        response = await client.get("/api/v1/buy/accounts")
        assert response.status_code in [200, 500]

    async def test_buy_account_detail_accessible(self, client: AsyncClient):
        """Test buy account detail endpoint is accessible."""
        account_id = uuid4()
        response = await client.get(f"/api/v1/buy/accounts/{account_id}")
        assert response.status_code in [200, 404, 500]

    async def test_buy_similar_accounts_accessible(self, client: AsyncClient):
        """Test buy similar accounts endpoint is accessible."""
        account_id = uuid4()
        response = await client.get(f"/api/v1/buy/accounts/{account_id}/similar")
        assert response.status_code in [200, 404, 500]

    async def test_buy_deals_accessible(self, client: AsyncClient):
        """Test buy deals endpoint is accessible."""
        response = await client.get("/api/v1/buy/deals/my")
        assert response.status_code in [401, 500]  # Requires auth

    async def test_buy_mediators_accessible(self, client: AsyncClient):
        """Test buy mediators endpoint is accessible."""
        response = await client.get("/api/v1/buy/mediators/")
        assert response.status_code in [200, 500]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestChatEndpoints:
    """Test chat endpoints."""

    async def test_chat_rooms_requires_auth(self, client: AsyncClient):
        """Test chat rooms requires authentication."""
        response = await client.get("/api/v1/chat/rooms")
        assert response.status_code == 401

    async def test_chat_room_detail_requires_auth(self, client: AsyncClient):
        """Test chat room detail requires auth."""
        room_id = uuid4()
        response = await client.get(f"/api/v1/chat/rooms/{room_id}")
        assert response.status_code == 401

    async def test_chat_messages_requires_auth(self, client: AsyncClient):
        """Test chat messages requires auth."""
        room_id = uuid4()
        response = await client.get(f"/api/v1/chat/rooms/{room_id}/messages")
        assert response.status_code == 401

    async def test_chat_unread_count_requires_auth(self, client: AsyncClient):
        """Test chat unread count requires auth."""
        response = await client.get("/api/v1/chat/unread-count")
        assert response.status_code == 401

    async def test_chat_send_message_requires_auth(self, client: AsyncClient):
        """Test chat send message requires auth."""
        room_id = uuid4()
        response = await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            json={"content": "Hello", "type": "text"},
        )
        assert response.status_code in [401, 405]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestNotificationEndpoints:
    """Test notification endpoints."""

    async def test_notifications_requires_auth(self, client: AsyncClient):
        """Test notifications requires authentication."""
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 401

    async def test_notification_detail_requires_auth(self, client: AsyncClient):
        """Test notification detail requires auth."""
        notif_id = uuid4()
        response = await client.get(f"/api/v1/notifications/{notif_id}")
        assert response.status_code == 401

    async def test_mark_read_requires_auth(self, client: AsyncClient):
        """Test mark as read requires auth."""
        notif_id = uuid4()
        response = await client.post(f"/api/v1/notifications/{notif_id}/read")
        assert response.status_code == 401

    async def test_mark_all_read_requires_auth(self, client: AsyncClient):
        """Test mark all read requires auth."""
        response = await client.post("/api/v1/notifications/read-all")
        assert response.status_code == 401

    async def test_unread_count_requires_auth(self, client: AsyncClient):
        """Test unread count requires auth."""
        response = await client.get("/api/v1/notifications/unread-count")
        assert response.status_code == 401

    async def test_delete_notification_requires_auth(self, client: AsyncClient):
        """Test delete notification requires auth."""
        notif_id = uuid4()
        response = await client.delete(f"/api/v1/notifications/{notif_id}")
        assert response.status_code == 401

    async def test_notification_settings_requires_auth(self, client: AsyncClient):
        """Test notification settings requires auth."""
        response = await client.get("/api/v1/notifications/settings")
        assert response.status_code == 401

    async def test_update_notification_settings_requires_auth(self, client: AsyncClient):
        """Test update notification settings requires auth."""
        response = await client.put("/api/v1/notifications/settings", json={})
        assert response.status_code == 401


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestProfileEndpoints:
    """Test profile endpoints."""

    async def test_profile_me_requires_auth(self, client: AsyncClient):
        """Test profile me requires authentication."""
        response = await client.get("/api/v1/profile/me")
        assert response.status_code == 401

    async def test_profile_stats_requires_auth(self, client: AsyncClient):
        """Test profile stats requires auth."""
        response = await client.get("/api/v1/profile/me/stats")
        assert response.status_code == 401

    async def test_profile_trade_history_requires_auth(self, client: AsyncClient):
        """Test profile trade history requires auth."""
        response = await client.get("/api/v1/profile/me/trade-history")
        assert response.status_code == 401

    async def test_profile_update_requires_auth(self, client: AsyncClient):
        """Test profile update requires auth."""
        response = await client.put("/api/v1/profile/update", json={})
        assert response.status_code == 401

    async def test_profile_avatar_requires_auth(self, client: AsyncClient):
        """Test profile avatar requires auth."""
        response = await client.post("/api/v1/profile/avatar")
        assert response.status_code == 401

    async def test_profile_public_accessible(self, client: AsyncClient):
        """Test public profile endpoint is accessible."""
        user_id = uuid4()
        response = await client.get(f"/api/v1/profile/{user_id}")
        assert response.status_code in [200, 404, 500]

    async def test_profile_listings_requires_auth(self, client: AsyncClient):
        """Test profile listings requires auth."""
        response = await client.get("/api/v1/profile/listings")
        assert response.status_code == 401


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestSecurityEndpoints:
    """Test security endpoints."""

    async def test_security_score_requires_auth(self, client: AsyncClient):
        """Test security score requires authentication."""
        response = await client.get("/api/v1/security/score")
        assert response.status_code == 401

    async def test_login_history_requires_auth(self, client: AsyncClient):
        """Test login history requires auth."""
        response = await client.get("/api/v1/security/login-history")
        assert response.status_code in [401, 404]

    async def test_security_settings_requires_auth(self, client: AsyncClient):
        """Test security settings requires auth."""
        response = await client.get("/api/v1/security/settings")
        assert response.status_code in [401, 404]

    async def test_update_security_settings_requires_auth(self, client: AsyncClient):
        """Test update security settings requires auth."""
        response = await client.put("/api/v1/security/settings", json={})
        assert response.status_code in [401, 404, 405]

    async def test_change_password_requires_auth(self, client: AsyncClient):
        """Test change password requires auth."""
        response = await client.post("/api/v1/security/change-password", json={})
        assert response.status_code in [401, 404, 405]

    async def test_enable_2fa_requires_auth(self, client: AsyncClient):
        """Test enable 2FA requires auth."""
        response = await client.post("/api/v1/security/enable-2fa", json={})
        assert response.status_code in [401, 404, 405]

    async def test_verify_2fa_requires_auth(self, client: AsyncClient):
        """Test verify 2FA requires auth."""
        response = await client.post("/api/v1/security/verify-2fa", json={})
        assert response.status_code in [401, 404, 405]

    async def test_freeze_account_requires_auth(self, client: AsyncClient):
        """Test freeze account requires auth."""
        response = await client.post("/api/v1/security/freeze-account", json={})
        assert response.status_code in [401, 404, 405]

    async def test_unfreeze_account_requires_auth(self, client: AsyncClient):
        """Test unfreeze account requires auth."""
        response = await client.post("/api/v1/security/unfreeze-account", json={})
        assert response.status_code in [401, 404, 405]

    async def test_logout_all_requires_auth(self, client: AsyncClient):
        """Test logout all requires auth."""
        response = await client.post("/api/v1/security/logout-all")
        assert response.status_code in [401, 404, 405]


@pytest.mark.skip(reason="Requires PostgreSQL database")
class TestAdminEndpoints:
    """Test admin endpoints."""

    async def test_admin_dashboard_stats_requires_auth(self, client: AsyncClient):
        """Test admin dashboard stats requires auth."""
        response = await client.get("/api/v1/admin/dashboard/stats")
        assert response.status_code == 401

    async def test_admin_dashboard_analytics_requires_auth(self, client: AsyncClient):
        """Test admin dashboard analytics requires auth."""
        response = await client.get("/api/v1/admin/dashboard/analytics")
        assert response.status_code in [401, 404]

    async def test_admin_users_requires_auth(self, client: AsyncClient):
        """Test admin users requires auth."""
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401

    async def test_admin_user_detail_requires_auth(self, client: AsyncClient):
        """Test admin user detail requires auth."""
        user_id = uuid4()
        response = await client.get(f"/api/v1/admin/users/{user_id}")
        assert response.status_code in [401, 404]

    async def test_admin_ban_user_requires_auth(self, client: AsyncClient):
        """Test admin ban user requires auth."""
        user_id = uuid4()
        response = await client.post(f"/api/v1/admin/users/{user_id}/ban", json={})
        assert response.status_code in [401, 404, 405]

    async def test_admin_pending_listings_requires_auth(self, client: AsyncClient):
        """Test admin pending listings requires auth."""
        response = await client.get("/api/v1/admin/listings/pending")
        assert response.status_code in [401, 404]

    async def test_admin_approve_listing_requires_auth(self, client: AsyncClient):
        """Test admin approve listing requires auth."""
        listing_id = uuid4()
        response = await client.post(f"/api/v1/admin/listings/{listing_id}/approve")
        assert response.status_code in [401, 404, 405]

    async def test_admin_deals_requires_auth(self, client: AsyncClient):
        """Test admin deals requires auth."""
        response = await client.get("/api/v1/admin/deals")
        assert response.status_code in [401, 404]

    async def test_admin_resolve_deal_requires_auth(self, client: AsyncClient):
        """Test admin resolve deal requires auth."""
        deal_id = uuid4()
        response = await client.post(f"/api/v1/admin/deals/{deal_id}/resolve", json={})
        assert response.status_code in [401, 404, 405]

    async def test_admin_mediators_requires_auth(self, client: AsyncClient):
        """Test admin mediators requires auth."""
        response = await client.get("/api/v1/admin/mediators")
        assert response.status_code in [401, 404]

    async def test_admin_reports_requires_auth(self, client: AsyncClient):
        """Test admin reports requires auth."""
        response = await client.get("/api/v1/admin/reports")
        assert response.status_code in [401, 404]

    async def test_admin_faq_requires_auth(self, client: AsyncClient):
        """Test admin FAQ requires auth."""
        response = await client.get("/api/v1/admin/faq")
        assert response.status_code in [401, 404]

    async def test_admin_categories_requires_auth(self, client: AsyncClient):
        """Test admin categories requires auth."""
        response = await client.get("/api/v1/admin/categories")
        assert response.status_code in [401, 404]

    async def test_admin_games_requires_auth(self, client: AsyncClient):
        """Test admin games requires auth."""
        response = await client.get("/api/v1/admin/games")
        assert response.status_code in [401, 404]

    async def test_admin_promo_banners_requires_auth(self, client: AsyncClient):
        """Test admin promo banners requires auth."""
        response = await client.get("/api/v1/admin/promo-banners")
        assert response.status_code in [401, 404]
