"""Routers for API version 1."""

from .auth import router as auth_router
from .health import router as health_router

__all__ = ["health_router", "auth_router"]
