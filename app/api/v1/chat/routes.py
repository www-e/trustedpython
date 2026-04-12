"""
Chat API routes - combines REST and WebSocket endpoints.

REST endpoints are imported from rest_routes.py
WebSocket endpoints are imported from websocket_routes.py
"""

from fastapi import APIRouter

from app.api.v1.chat.rest_routes import router as rest_router
from app.api.v1.chat.websocket_routes import router as ws_router

# Combine REST and WebSocket routers
router = APIRouter()

# Include REST routes
router.include_router(rest_router, tags=["Chat REST"])

# Include WebSocket routes
router.include_router(ws_router, tags=["Chat WebSocket"])
