"""API routing package."""

from app.api.web_routes import web_router
from app.api.test_routes import test_router

__all__ = ["web_router", "test_router"]
