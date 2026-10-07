"""Web pages router for serving server-rendered HTML templates and view workflows."""

import urllib.parse
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.controllers.user_controller import UserController

web_router = APIRouter(tags=["Web Pages"])

# Resolve template directory relative to the app module
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


async def _extract_form_data(request: Request) -> Dict[str, Any]:
    """Extracts form or payload data from HTML form or JSON request."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}

    # Try starlette form if python-multipart is available
    try:
        form = await request.form()
        return dict(form)
    except Exception:
        pass

    # Fallback to standard urlencoded body parsing without external dependencies
    try:
        body_bytes = await request.body()
        if body_bytes:
            parsed = urllib.parse.parse_qs(body_bytes.decode("utf-8"))
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
    except Exception:
        pass

    return {}


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


@web_router.get(
    "/users",
    response_class=HTMLResponse,
    summary="Web Users Listing Page",
    description="Renders the HTML View listing all alumni/users and providing a user creation form.",
)
async def get_web_users(request: Request):
    """Web route rendering the HTML users list page via UserController."""
    user_context = UserController.get_users()
    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "users": user_context.get("users", []),
            "user_count": user_context.get("count", 0),
        },
    )


@web_router.post(
    "/users",
    response_class=HTMLResponse,
    summary="Web Create User via View Form",
    description="Processes user creation from the HTML View form and returns the updated users list View.",
)
async def create_web_user(request: Request):
    """Web route creating a user from form data via UserController and returning the View."""
    raw_data = await _extract_form_data(request)

    # Cast graduation_year to integer if provided as numeric string
    if "graduation_year" in raw_data and raw_data["graduation_year"] != "":
        try:
            raw_data["graduation_year"] = int(raw_data["graduation_year"])
        except (ValueError, TypeError):
            pass

    create_res = UserController.create_user(raw_data)
    user_context = UserController.get_users()

    if create_res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="users/list.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "users": user_context.get("users", []),
                "user_count": user_context.get("count", 0),
                "success_message": "Kullanıcı başarıyla oluşturuldu.",
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="users/list.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "users": user_context.get("users", []),
                "user_count": user_context.get("count", 0),
                "error_message": create_res.get("message")
                or "Kullanıcı oluşturulurken bir hata oluştu.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.get("/users/{id}", summary="Web User Details")
async def get_web_user(id: int):
    """Web route retrieving a single user by ID via UserController."""
    return UserController.get_user(id)


@web_router.put("/users/{id}", summary="Web Update User")
async def update_web_user(id: int, payload: dict):
    """Web route updating a user via UserController."""
    return UserController.update_user(id, payload)


@web_router.delete("/users/{id}", summary="Web Delete User")
async def delete_web_user(id: int):
    """Web route deleting a user via UserController."""
    return UserController.delete_user(id)
