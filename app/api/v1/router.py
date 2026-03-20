"""API v1 router."""

from fastapi import APIRouter

# Import domain routers here
from app.api.v1.auth import router as auth_router

api_router = APIRouter()

# Register domain routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
