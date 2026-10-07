"""Web pages router for serving server-rendered HTML templates."""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.controllers.user_controller import UserController

web_router = APIRouter(tags=["Web Pages"])

# Resolve template directory relative to the app module
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@web_router.get("/", response_class=HTMLResponse, summary="Landing Page")
async def get_landing_page(request: Request):
    """Renders the modern landing page for the Alumni Tracking System."""
    user_context = UserController.get_users()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "users": user_context.get("users", []),
            "user_count": user_context.get("count", 0),
        },
    )


@web_router.get("/about", response_class=HTMLResponse, summary="About Page")
async def get_about_page(request: Request):
    """Renders the comprehensive project About page."""
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
        },
    )


@web_router.get("/users", summary="Web Users Directory")
async def get_web_users():
    """Web route retrieving all users via UserController."""
    return UserController.get_users()


@web_router.get("/users/{id}", summary="Web User Details")
async def get_web_user(id: int):
    """Web route retrieving a single user by ID via UserController."""
    return UserController.get_user(id)


@web_router.post("/users", summary="Web Create User")
async def create_web_user(payload: dict):
    """Web route creating a user via UserController."""
    return UserController.create_user(payload)


@web_router.put("/users/{id}", summary="Web Update User")
async def update_web_user(id: int, payload: dict):
    """Web route updating a user via UserController."""
    return UserController.update_user(id, payload)


@web_router.delete("/users/{id}", summary="Web Delete User")
async def delete_web_user(id: int):
    """Web route deleting a user via UserController."""
    return UserController.delete_user(id)
