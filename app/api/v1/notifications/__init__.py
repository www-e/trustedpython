"""Notification API v1 routes."""

from fastapi import APIRouter

from app.api.v1.notifications.routes import router

__all__ = ["router"]
