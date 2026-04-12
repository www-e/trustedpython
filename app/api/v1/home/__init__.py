"""Home feed API module."""

from fastapi import APIRouter

from app.api.v1.home.routes import router as home_router

router = APIRouter()

# Include home feed routes
router.include_router(home_router, tags=["Home Feed"])
