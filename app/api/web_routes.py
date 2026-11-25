"""Web pages router for serving server-rendered HTML templates and view workflows."""

import urllib.parse
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.csrf import generate_login_csrf_token
from app.core.database import get_db_session
from app.core.dependencies import get_current_user, get_current_user_optional, require_role
from app.controllers.announcement_controller import AnnouncementController
from app.controllers.user_controller import UserController
from app.models.announcement import AnnouncementDB
from app.models.application import ApplicationDB
from app.models.job_posting import JobPostingDB
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.registration_service import RegistrationService
from app.services.session_service import SessionService

web_router = APIRouter(tags=["Web Pages"])

# Resolve template directory relative to the app module
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _is_json_requested(request: Request) -> bool:
    """Checks whether the client specifically requested JSON response."""
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type", "")
    return "application/json" in accept and "text/html" not in accept


def _is_html_requested(request: Request) -> bool:
    """Checks whether the client requested HTML or submitted standard browser form."""
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type", "")
    return (
        "text/html" in accept
        or "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    )


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
            parsed = urllib.parse.parse_qs(
                body_bytes.decode("utf-8"), keep_blank_values=True
            )
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


def _check_web_user_permission(request: Request, target_user_id: int):
    """Enforces that caller is either the user themselves or has admin role."""
    current_user = getattr(request.state, "user", None)
    if not current_user or (current_user.get("user_id") != target_user_id and current_user.get("role") != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu profil üzerinde işlem yapma yetkiniz bulunmamaktadır.",
        )


def _check_web_announcement_permission(request: Request, announcement_id: int):
    """Enforces that caller is either an admin or the author (academician)."""
    current_user = getattr(request.state, "user", None)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor.",
        )

    user_role = current_user.get("role")
    if user_role == "admin":
        return

    if user_role != "academician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu duyuruyu değiştirme veya silme yetkiniz bulunmamaktadır.",
        )

    res = AnnouncementController.get_announcement(announcement_id)
    if not res.get("success") or not res.get("announcement"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duyuru bulunamadı (ID: {announcement_id}).",
        )

    ann = res["announcement"]
    author_id = getattr(ann, "created_by", None)
    if isinstance(ann, dict):
        author_id = ann.get("created_by")

    if author_id is None or author_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu duyuruyu değiştirme veya silme yetkiniz bulunmamaktadır.",
        )


@web_router.post(
    "/users",
    response_class=HTMLResponse,
    summary="Web Create User via View Form",
    description="Processes user creation from the HTML View form and returns the updated users list View (Admin only).",
)
async def create_web_user(request: Request):
    """Web route creating a user from form data via UserController (Admin only)."""
    current_user = getattr(request.state, "user", None)
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yalnızca yöneticiler doğrudan kullanıcı oluşturabilir.",
        )

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
    _check_web_user_permission(request, id)
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
    _check_web_user_permission(request, id)
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
    _check_web_user_permission(request, id)
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
    _check_web_user_permission(request, id)
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
    _check_web_user_permission(request, id)
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


# -----------------------------------------------------------------------------
# Web Announcements CRUD (Coordinating with AnnouncementController & View)
# -----------------------------------------------------------------------------


@web_router.get(
    "/announcements",
    response_class=HTMLResponse,
    summary="Web Announcements Listing Page",
    description="Renders the HTML View listing all announcements or returns JSON if requested.",
)
@web_router.get(
    "/announcements/",
    include_in_schema=False,
)
async def get_web_announcements(request: Request):
    """Web route retrieving all announcements via AnnouncementController."""
    res = AnnouncementController.get_announcements()
    if _is_html_requested(request):
        return templates.TemplateResponse(
            request=request,
            name="announcements/list.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "announcements": res.get("announcements", []),
                "announcement_count": res.get("count", 0),
            },
        )
    return JSONResponse(content=jsonable_encoder(res), status_code=status.HTTP_200_OK)


@web_router.post(
    "/announcements",
    response_class=HTMLResponse,
    summary="Web Create Announcement via View Form",
    description="Processes announcement creation from HTML form or JSON payload via AnnouncementController.",
)
@web_router.post(
    "/announcements/",
    include_in_schema=False,
)
async def create_web_announcement(request: Request):
    """Web route creating an announcement via AnnouncementController."""
    current_user = getattr(request.state, "user", None)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor.",
        )

    user_role = current_user.get("role")
    if user_role not in ("admin", "academician"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Duyuru oluşturma yetkiniz bulunmamaktadır. Yalnızca yönetici veya akademisyenler duyuru yayınlayabilir.",
        )

    raw_data = await _extract_form_data(request)
    if "created_by" in raw_data and raw_data["created_by"] is not None and raw_data["created_by"] != "":
        try:
            raw_data["created_by"] = int(raw_data["created_by"])
        except (ValueError, TypeError):
            pass
    elif "created_by" in raw_data and raw_data["created_by"] == "":
        raw_data["created_by"] = None

    if user_role != "admin" or not raw_data.get("created_by"):
        raw_data["created_by"] = current_user.get("user_id")

    create_res = AnnouncementController.create_announcement(raw_data)

    if _is_html_requested(request):
        announcement_context = AnnouncementController.get_announcements()
        if create_res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="announcements/list.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcements": announcement_context.get("announcements", []),
                    "announcement_count": announcement_context.get("count", 0),
                    "success_message": "Duyuru başarıyla yayınlandı.",
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="announcements/list.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcements": announcement_context.get("announcements", []),
                    "announcement_count": announcement_context.get("count", 0),
                    "error_message": create_res.get("message")
                    or "Duyuru oluşturulurken bir hata oluştu.",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    status_code = status.HTTP_200_OK if create_res.get("success") else status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=jsonable_encoder(create_res), status_code=status_code)


@web_router.get(
    "/announcements/{id}",
    response_class=HTMLResponse,
    summary="Web Announcement Details Page",
    description="Retrieves a single announcement by ID via AnnouncementController; renders detail HTML view or returns JSON.",
)
async def get_web_announcement(request: Request, id: int):
    """Web route retrieving a single announcement by ID via AnnouncementController."""
    res = AnnouncementController.get_announcement(id)
    if _is_html_requested(request):
        if res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="announcements/detail.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": res.get("announcement"),
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="announcements/detail.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": None,
                    "error_message": res.get("message") or f"Duyuru #{id} bulunamadı.",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

    status_code = status.HTTP_200_OK if res.get("success") else status.HTTP_404_NOT_FOUND
    return JSONResponse(content=jsonable_encoder(res), status_code=status_code)


@web_router.get(
    "/announcements/{id}/edit",
    response_class=HTMLResponse,
    summary="Web Edit Announcement Form Page",
    description="Renders the pre-filled HTML View form to edit an existing announcement via AnnouncementController.",
)
async def get_web_announcement_edit_form(request: Request, id: int):
    """Web route rendering edit announcement form pre-filled via AnnouncementController."""
    _check_web_announcement_permission(request, id)
    res = AnnouncementController.get_announcement(id)
    if res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="announcements/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "announcement": res.get("announcement"),
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="announcements/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "announcement": None,
                "error_message": res.get("message") or f"Düzenlenecek duyuru #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.post(
    "/announcements/{id}/edit",
    response_class=HTMLResponse,
    summary="Web Update Announcement via Edit Form",
    description="Processes announcement update from edit View form and returns the updated announcement detail View.",
)
@web_router.post(
    "/announcements/{id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def update_web_announcement_form(request: Request, id: int):
    """Web route handling browser form POST for announcement updates."""
    _check_web_announcement_permission(request, id)
    raw_data = await _extract_form_data(request)
    if "created_by" in raw_data and raw_data["created_by"] is not None and raw_data["created_by"] != "":
        try:
            raw_data["created_by"] = int(raw_data["created_by"])
        except (ValueError, TypeError):
            pass
    current_user = getattr(request.state, "user", {}) or {}
    if current_user.get("role") != "admin":
        raw_data.pop("created_by", None)

    update_res = AnnouncementController.update_announcement(id, raw_data)

    if _is_html_requested(request):
        if update_res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="announcements/detail.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": update_res.get("announcement"),
                    "success_message": "Duyuru başarıyla güncellendi.",
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            existing_res = AnnouncementController.get_announcement(id)
            if not existing_res.get("success"):
                return templates.TemplateResponse(
                    request=request,
                    name="announcements/edit.html",
                    context={
                        "app_name": settings.APP_NAME,
                        "app_title_tr": settings.APP_TITLE_TR,
                        "app_description": settings.APP_DESCRIPTION,
                        "app_version": settings.APP_VERSION,
                        "announcement": None,
                        "error_message": update_res.get("message") or f"Duyuru #{id} bulunamadı.",
                    },
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            return templates.TemplateResponse(
                request=request,
                name="announcements/edit.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": {**existing_res["announcement"].model_dump(), **raw_data, "id": id},
                    "error_message": update_res.get("message") or "Duyuru güncellenirken bir hata oluştu.",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    status_code = status.HTTP_200_OK if update_res.get("success") else status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=jsonable_encoder(update_res), status_code=status_code)


@web_router.put(
    "/announcements/{id}",
    summary="Web Update Announcement (PUT)",
    description="Updates an announcement via AnnouncementController; supports JSON payload and form updates.",
)
async def update_web_announcement(id: int, request: Request):
    """Web route updating an announcement via AnnouncementController (PUT)."""
    _check_web_announcement_permission(request, id)
    raw_data = await _extract_form_data(request)
    if "created_by" in raw_data and raw_data["created_by"] is not None and raw_data["created_by"] != "":
        try:
            raw_data["created_by"] = int(raw_data["created_by"])
        except (ValueError, TypeError):
            pass
    current_user = getattr(request.state, "user", {}) or {}
    if current_user.get("role") != "admin":
        raw_data.pop("created_by", None)

    res = AnnouncementController.update_announcement(id, raw_data)

    if _is_html_requested(request):
        if res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="announcements/detail.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": res.get("announcement"),
                    "success_message": "Duyuru başarıyla güncellendi.",
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="announcements/edit.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcement": None,
                    "error_message": res.get("message") or f"Duyuru #{id} bulunamadı.",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

    status_code = status.HTTP_200_OK if res.get("success") else status.HTTP_404_NOT_FOUND
    return JSONResponse(content=jsonable_encoder(res), status_code=status_code)


@web_router.post(
    "/announcements/{id}/delete",
    response_class=HTMLResponse,
    summary="Web Delete Announcement via Form",
    description="Processes announcement deletion from browser form and returns the updated announcements list View.",
)
async def delete_web_announcement_form(request: Request, id: int):
    """Web route handling browser form POST for announcement deletion."""
    _check_web_announcement_permission(request, id)
    del_res = AnnouncementController.delete_announcement(id)
    announcements_context = AnnouncementController.get_announcements()

    if del_res.get("success"):
        return templates.TemplateResponse(
            request=request,
            name="announcements/list.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "announcements": announcements_context.get("announcements", []),
                "announcement_count": announcements_context.get("count", 0),
                "success_message": f"Duyuru #{id} başarıyla silindi.",
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="announcements/list.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "announcements": announcements_context.get("announcements", []),
                "announcement_count": announcements_context.get("count", 0),
                "error_message": del_res.get("message") or f"Duyuru #{id} bulunamadı.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )


@web_router.delete(
    "/announcements/{id}",
    summary="Web Delete Announcement (DELETE)",
    description="Deletes an announcement via AnnouncementController.",
)
async def delete_web_announcement(request: Request, id: int):
    """Web route deleting an announcement via AnnouncementController (DELETE)."""
    _check_web_announcement_permission(request, id)
    del_res = AnnouncementController.delete_announcement(id)

    if _is_html_requested(request):
        announcements_context = AnnouncementController.get_announcements()
        if del_res.get("success"):
            return templates.TemplateResponse(
                request=request,
                name="announcements/list.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcements": announcements_context.get("announcements", []),
                    "announcement_count": announcements_context.get("count", 0),
                    "success_message": f"Duyuru #{id} başarıyla silindi.",
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="announcements/list.html",
                context={
                    "app_name": settings.APP_NAME,
                    "app_title_tr": settings.APP_TITLE_TR,
                    "app_description": settings.APP_DESCRIPTION,
                    "app_version": settings.APP_VERSION,
                    "announcements": announcements_context.get("announcements", []),
                    "announcement_count": announcements_context.get("count", 0),
                    "error_message": del_res.get("message") or f"Duyuru #{id} bulunamadı.",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

    status_code = status.HTTP_200_OK if del_res.get("success") else status.HTTP_404_NOT_FOUND
    return JSONResponse(content=jsonable_encoder(del_res), status_code=status_code)


# --------------------------------------------------------------------------
# User Registration & Login Landing Routes
# --------------------------------------------------------------------------

@web_router.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """Renders the alumni user registration page."""
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "form_data": {},
            "error_message": None,
            "success_message": None,
            "registered_user": None,
        },
        status_code=status.HTTP_200_OK,
    )


@web_router.post("/register")
async def post_register_page(request: Request):
    """Handles alumni user registration form submissions and JSON requests."""
    form_data = await _extract_form_data(request)

    try:
        registered = RegistrationService.register_user(form_data)
        if _is_json_requested(request):
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Kullanıcı kaydı başarıyla oluşturuldu.",
                    "data": registered,
                },
                status_code=status.HTTP_201_CREATED,
            )

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "form_data": {},
                "error_message": None,
                "success_message": "Kaydınız başarıyla tamamlandı! Giriş yapabilirsiniz.",
                "registered_user": registered,
            },
            status_code=status.HTTP_200_OK,
        )
    except ValueError as e:
        err_msg = str(e)
        if _is_json_requested(request):
            return JSONResponse(
                content={
                    "status": "error",
                    "message": err_msg,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        preserved = {
            "name": form_data.get("name", ""),
            "email": form_data.get("email", ""),
            "department": form_data.get("department", ""),
            "graduation_year": form_data.get("graduation_year", ""),
        }
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "form_data": preserved,
                "error_message": err_msg,
                "success_message": None,
                "registered_user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.post("/api/register")
async def api_register_user(request: Request):
    """REST API registration endpoint accepting JSON payload."""
    form_data = await _extract_form_data(request)
    try:
        registered = RegistrationService.register_user(form_data)
        return JSONResponse(
            content={
                "status": "success",
                "message": "Kullanıcı kaydı başarıyla oluşturuldu.",
                "data": registered,
            },
            status_code=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """Renders the login page. Redirects to dashboard if already authenticated."""
    current_user = get_current_user_optional(request)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    notice = request.query_params.get("notice")
    csrf_token = generate_login_csrf_token()
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "form_data": {},
            "csrf_token": csrf_token,
            "error_message": None,
            "notice_message": notice,
            "user": None,
        },
        status_code=status.HTTP_200_OK,
    )


@web_router.post("/login")
async def post_login_page(request: Request):
    """Handles login submissions from HTML form and JSON API."""
    form_data = await _extract_form_data(request)
    email = form_data.get("email", "")
    password = form_data.get("password", "")

    try:
        session_token, user_data = AuthService.authenticate_user(email=email, password=password)

        if _is_json_requested(request):
            response = JSONResponse(
                content={
                    "status": "success",
                    "message": "Giriş başarılı.",
                    "data": user_data,
                    "csrf_token": user_data.get("csrf_token"),
                    "redirect_url": "/dashboard",
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            response = RedirectResponse(
                url="/dashboard",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # Set secure session cookie
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.session_cookie_secure,
            path="/",
        )
        return response

    except ValueError as e:
        err_msg = str(e)
        if _is_json_requested(request):
            return JSONResponse(
                content={
                    "status": "error",
                    "message": err_msg,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "app_version": settings.APP_VERSION,
                "form_data": {"email": email},
                "csrf_token": generate_login_csrf_token(),
                "error_message": err_msg,
                "notice_message": None,
                "user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.post("/api/login")
async def api_login_user(request: Request):
    """REST API endpoint for user authentication."""
    form_data = await _extract_form_data(request)
    email = form_data.get("email", "")
    password = form_data.get("password", "")

    try:
        session_token, user_data = AuthService.authenticate_user(email=email, password=password)
        response = JSONResponse(
            content={
                "status": "success",
                "message": "Giriş başarılı.",
                "data": user_data,
                "csrf_token": user_data.get("csrf_token"),
                "redirect_url": "/dashboard",
            },
            status_code=status.HTTP_200_OK,
        )
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.session_cookie_secure,
            path="/",
        )
        return response
    except ValueError as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@web_router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    """Protected user dashboard view requiring active session with role-specific experiences."""
    user = get_current_user_optional(request)
    if not user:
        if _is_json_requested(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Oturum açmanız gerekiyor.",
            )
        return RedirectResponse(
            url="/login?notice=Panelinize+erişmek+için+lütfen+giriş+yapın.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user_id = user.get("user_id")
    role = user.get("role", "alumnus")

    # Safe sanitized profile data (preventing leak of password hashes or session secrets)
    profile_data = {
        "user_id": user_id,
        "name": user.get("name"),
        "email": user.get("email"),
        "role": role,
        "department": user.get("department") or "Belirtilmedi",
        "graduation_year": user.get("graduation_year"),
    }

    recent_jobs = []
    user_applications = []
    recent_announcements = []
    my_announcements = []
    system_stats = {}

    try:
        with get_db_session() as db:
            # 1. Latest announcements (relevant across roles)
            announcement_records = (
                db.query(AnnouncementDB)
                .order_by(AnnouncementDB.id.desc())
                .limit(4)
                .all()
            )
            recent_announcements = [
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "created_by": a.created_by,
                }
                for a in announcement_records
            ]

            # 2. Role-specific information queries
            if role in ("alumnus", "student"):
                # Job opportunities
                job_records = (
                    db.query(JobPostingDB)
                    .order_by(JobPostingDB.id.desc())
                    .limit(4)
                    .all()
                )
                recent_jobs = [
                    {
                        "id": j.id,
                        "title": j.title,
                        "company_name": j.company_name,
                        "location": j.location or "Belirtilmedi",
                        "employment_type": j.employment_type or "Tam Zamanlı",
                        "description": j.description or "",
                    }
                    for j in job_records
                ]

                # Application history
                app_records = (
                    db.query(ApplicationDB, JobPostingDB)
                    .join(JobPostingDB, ApplicationDB.job_posting_id == JobPostingDB.id)
                    .filter(ApplicationDB.user_id == user_id)
                    .order_by(ApplicationDB.id.desc())
                    .limit(5)
                    .all()
                )
                user_applications = [
                    {
                        "id": app.id,
                        "status": app.status,
                        "created_at": app.created_at,
                        "job_id": job.id,
                        "job_title": job.title,
                        "company_name": job.company_name,
                    }
                    for app, job in app_records
                ]

            elif role == "academician":
                # Announcements authored by this academician
                my_ann_records = (
                    db.query(AnnouncementDB)
                    .filter(AnnouncementDB.created_by == user_id)
                    .order_by(AnnouncementDB.id.desc())
                    .all()
                )
                my_announcements = [
                    {
                        "id": a.id,
                        "title": a.title,
                        "content": a.content,
                    }
                    for a in my_ann_records
                ]

            elif role == "admin":
                # System statistics aggregated from PostgreSQL
                system_stats = AdminService.get_system_stats()

    except Exception:
        pass

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": user,
            "profile": profile_data,
            "csrf_token": user.get("csrf_token"),
            "recent_jobs": recent_jobs,
            "user_applications": user_applications,
            "recent_announcements": recent_announcements,
            "my_announcements": my_announcements,
            "system_stats": system_stats,
        },
        status_code=status.HTTP_200_OK,
    )


@web_router.get("/api/me")
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Protected REST endpoint returning the authenticated user's profile."""
    return {
        "status": "success",
        "user": current_user,
    }


@web_router.get("/api/admin/overview")
async def get_admin_overview(
    admin_user: Dict[str, Any] = Depends(require_role("admin")),
):
    """Protected role-guarded endpoint accessible only to administrators."""
    return {
        "status": "success",
        "message": "Admin paneline hoş geldiniz.",
        "admin": admin_user,
    }


@web_router.post("/logout")
async def post_logout(request: Request):
    """Logs out authenticated user, invalidates session, clears cookie, and redirects."""
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_token:
        SessionService.delete_session(session_token)

    if _is_json_requested(request):
        response = JSONResponse(
            content={
                "status": "success",
                "message": "Oturum başarıyla kapatıldı.",
                "redirect_url": "/login",
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        response = RedirectResponse(
            url="/login?notice=Oturumunuz+başarıyla+kapatıldı.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )
    return response


@web_router.post("/api/logout")
async def api_logout_user(request: Request):
    """REST API endpoint for user logout and session invalidation."""
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_token:
        SessionService.delete_session(session_token)

    response = JSONResponse(
        content={
            "status": "success",
            "message": "Oturum başarıyla kapatıldı.",
            "redirect_url": "/login",
        },
        status_code=status.HTTP_200_OK,
    )
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
    )
    return response


@web_router.get("/logout")
async def get_logout_redirect(request: Request):
    """Safe GET handler; prevents GET-based logout CSRF and redirects to dashboard or login."""
    current_user = get_current_user_optional(request)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
