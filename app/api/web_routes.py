"""Web pages router for serving server-rendered HTML templates and view workflows."""

import urllib.parse
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.controllers.user_controller import UserController

web_router = APIRouter(tags=["Web Pages"])

# Resolve template directory relative to the app module
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _is_json_requested(request: Request) -> bool:
    """Checks whether the client specifically requested JSON response."""
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type", "")
    return "application/json" in accept and "text/html" not in accept


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


# -----------------------------------------------------------------------------
# Static / Landing Pages
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Web Users CRUD (View Layer)
# -----------------------------------------------------------------------------


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

    if _is_json_requested(request):
        status_code = status.HTTP_201_CREATED if create_res.get("success") else status.HTTP_400_BAD_REQUEST
        return JSONResponse(content=jsonable_encoder(create_res), status_code=status_code)

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


@web_router.get(
    "/users/{id}",
    response_class=HTMLResponse,
    summary="Web User Details Page",
    description="Renders the HTML View displaying details of a single user via UserController.",
)
async def get_web_user(request: Request, id: int):
    """Web route rendering single user details via UserController."""
    res = UserController.get_user(id)

    if _is_json_requested(request):
        status_code = status.HTTP_200_OK if res.get("success") else status.HTTP_404_NOT_FOUND
        return JSONResponse(content=jsonable_encoder(res), status_code=status_code)

    if res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="users/detail.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": res.get("user"),
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="users/detail.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": None,
                "error_message": res.get("message") or f"Kullanıcı #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.get(
    "/users/{id}/edit",
    response_class=HTMLResponse,
    summary="Web Edit User Form Page",
    description="Renders the pre-filled HTML View form to edit an existing user via UserController.",
)
async def get_web_user_edit_form(request: Request, id: int):
    """Web route rendering edit user form pre-filled via UserController."""
    res = UserController.get_user(id)

    if res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": res.get("user"),
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": None,
                "error_message": res.get("message") or f"Düzenlenecek kullanıcı #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.post(
    "/users/{id}/edit",
    response_class=HTMLResponse,
    summary="Web Update User via Edit Form",
    description="Processes update submission from the edit View form and returns the updated user detail View.",
)
@web_router.post(
    "/users/{id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def update_web_user_form(request: Request, id: int):
    """Web route handling browser form POST for user updates."""
    raw_data = await _extract_form_data(request)

    if "graduation_year" in raw_data and raw_data["graduation_year"] != "":
        try:
            raw_data["graduation_year"] = int(raw_data["graduation_year"])
        except (ValueError, TypeError):
            pass

    update_res = UserController.update_user(id, user_or_name=raw_data)

    if _is_json_requested(request):
        status_code = status.HTTP_200_OK if update_res.get("success") else status.HTTP_400_BAD_REQUEST
        return JSONResponse(content=jsonable_encoder(update_res), status_code=status_code)

    if update_res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="users/detail.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": update_res.get("user"),
                "success_message": "Kullanıcı başarıyla güncellendi.",
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        # Check if user existed
        existing_res = UserController.get_user(id)
        if not existing_res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="users/edit.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "user": None,
                    "error_message": update_res.get("message") or f"Kullanıcı #{id} bulunamadı.",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validation error on existing user
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": {**existing_res["user"].model_dump(), **raw_data, "id": id},
                "error_message": update_res.get("message")
                or "Kullanıcı güncellenirken bir hata oluştu.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.put(
    "/users/{id}",
    summary="Web Update User (PUT)",
    description="Updates a user via UserController; supports both JSON payload and form updates.",
)
async def update_web_user(request: Request, id: int):
    """Web route updating a user via UserController (PUT)."""
    raw_data = await _extract_form_data(request)

    if "graduation_year" in raw_data and raw_data["graduation_year"] != "":
        try:
            raw_data["graduation_year"] = int(raw_data["graduation_year"])
        except (ValueError, TypeError):
            pass

    update_res = UserController.update_user(id, user_or_name=raw_data)

    if _is_json_requested(request) or not request.headers.get("accept", "").startswith("text/html"):
        status_code = status.HTTP_200_OK if update_res.get("success") else status.HTTP_404_NOT_FOUND
        return JSONResponse(content=jsonable_encoder(update_res), status_code=status_code)

    if update_res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="users/detail.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": update_res.get("user"),
                "success_message": "Kullanıcı başarıyla güncellendi.",
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "user": None,
                "error_message": update_res.get("message") or f"Kullanıcı #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.post(
    "/users/{id}/delete",
    response_class=HTMLResponse,
    summary="Web Delete User via Form",
    description="Processes user deletion from browser form and returns the updated users list View.",
)
async def delete_web_user_form(request: Request, id: int):
    """Web route handling browser form POST for user deletion."""
    del_res = UserController.delete_user(id)
    user_context = UserController.get_users()

    if del_res.get("success"):
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
                "success_message": f"Kullanıcı #{id} başarıyla silindi.",
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
                "error_message": del_res.get("message") or f"Kullanıcı #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.delete(
    "/users/{id}",
    summary="Web Delete User (DELETE)",
    description="Deletes a user via UserController.",
)
async def delete_web_user(request: Request, id: int):
    """Web route deleting a user via UserController (DELETE)."""
    del_res = UserController.delete_user(id)

    if _is_json_requested(request) or not request.headers.get("accept", "").startswith("text/html"):
        status_code = status.HTTP_200_OK if del_res.get("success") else status.HTTP_404_NOT_FOUND
        return JSONResponse(content=jsonable_encoder(del_res), status_code=status_code)

    user_context = UserController.get_users()
    if del_res.get("success"):
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
                "success_message": f"Kullanıcı #{id} başarıyla silindi.",
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
                "error_message": del_res.get("message") or f"Kullanıcı #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
