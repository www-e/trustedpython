"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    admin,
    analytics,
    auth,
    buy,
    chat,
    games,
    home,
    notifications,
    orders,
    payments,
    profile,
    security,
    sell,
    users,
)
from app.api.v1.notifications import websocket as notifications_websocket

api_router = APIRouter()

# Include all module routers
# Modules with prefixes already defined in their __init__.py or routes files:
api_router.include_router(buy.router, tags=["Buying"])
api_router.include_router(sell.router, tags=["Selling"])
api_router.include_router(admin.router, tags=["Admin Dashboard"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
# Modules without prefixes - need to be added here:
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(home.router, prefix="/home", tags=["Home Feed"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(games.router, prefix="/games", tags=["Games"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(security.router, prefix="/security", tags=["Security"])

# WebSocket routes (chat WebSocket is already included in chat.router)
api_router.include_router(
    notifications_websocket.router, prefix="/notifications", tags=["Notifications WebSocket"]
)
