"""
Buy Flow API module.

Provides endpoints for account browsing, mediator selection,
deal creation, and payment processing.

This module has been refactored from a monolithic structure into
focused, single-responsibility route modules.
"""

from fastapi import APIRouter

from app.api.v1.buy import account_routes, deal_routes, mediator_routes, payment_routes

# Create main buy router
router = APIRouter(prefix="/buy", tags=["Buy Flow"])

# Include all sub-route modules
router.include_router(account_routes.router)
router.include_router(mediator_routes.router)
router.include_router(deal_routes.router)
router.include_router(payment_routes.router)

__all__ = ["router"]
