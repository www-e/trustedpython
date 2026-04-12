"""
Admin Dashboard API module.

Provides endpoints for platform management including user management,
listing moderation, deal oversight, mediator management, reports,
and platform configuration.

This module has been refactored from a monolithic structure into
focused, single-responsibility route modules.
"""

from fastapi import APIRouter

from app.api.v1.admin import (
    content_routes,
    dashboard_routes,
    deal_routes,
    listing_routes,
    mediator_routes,
    report_routes,
    user_routes,
)

# Create main admin router
router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# Include all sub-route modules
router.include_router(dashboard_routes.router, tags=["Dashboard"])
router.include_router(user_routes.router, tags=["User Management"])
router.include_router(listing_routes.router, tags=["Listing Moderation"])
router.include_router(deal_routes.router, tags=["Deal Management"])
router.include_router(mediator_routes.router, tags=["Mediator Management"])
router.include_router(report_routes.router, tags=["Reports"])
router.include_router(content_routes.router, tags=["Content Management"])

__all__ = ["router"]
