"""Chat API module - combines REST and WebSocket endpoints."""

from fastapi import APIRouter

from app.api.v1.chat.routes import router as combined_router

# Re-export the combined router from routes.py
router = combined_router

__all__ = ["router"]
