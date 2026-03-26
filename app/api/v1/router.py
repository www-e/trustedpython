"""API v1 router."""

from fastapi import APIRouter

# Import domain routers here
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.listings import router as listings_router
from app.api.v1.users import router as users_router
from app.api.v1.deals import router as deals_router
from app.api.v1.mediators import router as mediators_router
from app.api.v1.exclusive_cards import router as exclusive_cards_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Register domain routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(categories_router, tags=["Categories"])
api_router.include_router(listings_router, tags=["Listings"])
api_router.include_router(users_router, tags=["Users"])
api_router.include_router(deals_router, prefix="/deals", tags=["Deals"])
api_router.include_router(mediators_router, prefix="/mediators", tags=["Mediators"])
api_router.include_router(exclusive_cards_router, tags=["Exclusive Cards"])
api_router.include_router(admin_router, tags=["Admin"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
