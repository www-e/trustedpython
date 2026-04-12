"""Selling router module."""

from fastapi import APIRouter

from app.api.v1.sell.routes import router as routes_router

router = APIRouter(prefix="/sell", tags=["Selling"])
router.include_router(routes_router)
