"""Admin panel routes for managing users, jobs, applications, and announcements."""

from pathlib import Path
from typing import Any, Dict, Optional
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.dependencies import require_role
from app.services.admin_service import AdminService

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin Panel"],
    dependencies=[Depends(require_role("admin"))],
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _is_json_requested(request: Request) -> bool:
    """Detects whether client expects a JSON response."""
    accept = request.headers.get("accept", "").lower()
    content_type = request.headers.get("content-type", "").lower()
    return "application/json" in accept or "application/json" in content_type


async def _extract_payload(request: Request) -> Dict[str, Any]:
    """Safely extracts payload from form or JSON."""
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    try:
        form = await request.form()
        return dict(form)
    except Exception:
        return {}


# -----------------------------------------------------------------------------
# 1. Dashboard Overview
# -----------------------------------------------------------------------------
@admin_router.get("", response_class=HTMLResponse, summary="Admin Dashboard")
@admin_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_admin_dashboard(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Renders the admin dashboard with real-time aggregated PostgreSQL statistics."""
    stats = AdminService.get_system_stats()

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({
                "status": "success",
                "stats": stats,
                "admin": current_admin,
            })
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": current_admin,
            "csrf_token": current_admin.get("csrf_token"),
            "stats": stats,
        },
    )


# -----------------------------------------------------------------------------
# 2. Users Management
# -----------------------------------------------------------------------------
@admin_router.get("/users", response_class=HTMLResponse, summary="Admin Users List")
async def get_admin_users(
    request: Request,
    search: Optional[str] = Query(None, description="Search by name, email, department"),
    role: Optional[str] = Query(None, description="Filter by role"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Lists users with search, role filtering, and pagination."""
    result = AdminService.list_users(search=search, role=role, page=page, per_page=per_page)

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({
                "status": "success",
                **result,
            })
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": current_admin,
            "csrf_token": current_admin.get("csrf_token"),
            "users": result["users"],
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "pages": result["pages"],
            "current_role": role,
            "search": search,
        },
    )


@admin_router.post("/users/{user_id}/role", summary="Update User Role")
async def post_update_user_role(
    request: Request,
    user_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Updates user role with Last Admin Protection guard."""
    data = await _extract_payload(request)
    new_role = data.get("role")
    admin_id = current_admin.get("user_id") or current_admin.get("id")

    try:
        updated = AdminService.update_user_role(
            target_user_id=user_id, new_role=new_role, current_admin_id=admin_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Kullanıcı rolü güncellendi.", "user": updated})
        )

    return RedirectResponse(
        url="/admin/users?success=Kullanıcı+rolü+başarıyla+güncellendi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/users/{user_id}/edit", summary="Update User Details")
async def post_update_user_details(
    request: Request,
    user_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Updates user details with validation and demotion protection."""
    data = await _extract_payload(request)
    admin_id = current_admin.get("user_id") or current_admin.get("id")

    try:
        updated = AdminService.update_user_details(
            target_user_id=user_id, data=data, current_admin_id=admin_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Kullanıcı bilgileri güncellendi.", "user": updated})
        )

    return RedirectResponse(
        url="/admin/users?success=Kullanıcı+bilgileri+başarıyla+güncellendi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/users/{user_id}/delete", summary="Delete User")
async def post_delete_user(
    request: Request,
    user_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Deletes user with Self-Deletion and Last Admin Protection guards."""
    admin_id = current_admin.get("user_id") or current_admin.get("id")

    try:
        AdminService.delete_user(target_user_id=user_id, current_admin_id=admin_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Kullanıcı başarıyla silindi."})
        )

    return RedirectResponse(
        url="/admin/users?success=Kullanıcı+başarıyla+silindi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# -----------------------------------------------------------------------------
# 3. Job Postings Management
# -----------------------------------------------------------------------------
@admin_router.get("/jobs", response_class=HTMLResponse, summary="Admin Jobs List")
async def get_admin_jobs(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Lists all job postings with application counts."""
    jobs = AdminService.list_jobs()

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "jobs": jobs})
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/jobs.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": current_admin,
            "csrf_token": current_admin.get("csrf_token"),
            "jobs": jobs,
        },
    )


@admin_router.post("/jobs", summary="Create Job Posting")
async def post_create_job(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Creates a job posting."""
    data = await _extract_payload(request)
    try:
        created = AdminService.create_job(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "İş ilanı oluşturuldu.", "job": created})
        )

    return RedirectResponse(
        url="/admin/jobs?success=İş+ilanı+başarıyla+oluşturuldu.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/jobs/{job_id}/edit", summary="Update Job Posting")
async def post_update_job(
    request: Request,
    job_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Updates a job posting."""
    data = await _extract_payload(request)
    try:
        updated = AdminService.update_job(job_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "İş ilanı güncellendi.", "job": updated})
        )

    return RedirectResponse(
        url="/admin/jobs?success=İş+ilanı+başarıyla+güncellendi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/jobs/{job_id}/delete", summary="Delete Job Posting")
async def post_delete_job(
    request: Request,
    job_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Deletes a job posting and its applications."""
    try:
        AdminService.delete_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "İş ilanı silindi."})
        )

    return RedirectResponse(
        url="/admin/jobs?success=İş+ilanı+başarıyla+silindi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# -----------------------------------------------------------------------------
# 4. Applications Review & Management
# -----------------------------------------------------------------------------
@admin_router.get("/applications", response_class=HTMLResponse, summary="Admin Applications List")
async def get_admin_applications(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Lists all candidate applications."""
    applications = AdminService.list_applications()

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "applications": applications})
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/applications.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": current_admin,
            "csrf_token": current_admin.get("csrf_token"),
            "applications": applications,
        },
    )


@admin_router.post("/applications/{app_id}/status", summary="Update Application Status")
async def post_update_application_status(
    request: Request,
    app_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Updates status of a job application."""
    data = await _extract_payload(request)
    new_status = data.get("status")
    try:
        updated = AdminService.update_application_status(app_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Başvuru durumu güncellendi.", "application": updated})
        )

    return RedirectResponse(
        url="/admin/applications?success=Başvuru+durumu+güncellendi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/applications/{app_id}/delete", summary="Delete Application")
async def post_delete_application(
    request: Request,
    app_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Deletes an application."""
    try:
        AdminService.delete_application(app_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Başvuru silindi."})
        )

    return RedirectResponse(
        url="/admin/applications?success=Başvuru+silindi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# -----------------------------------------------------------------------------
# 5. Announcements Management
# -----------------------------------------------------------------------------
@admin_router.get("/announcements", response_class=HTMLResponse, summary="Admin Announcements List")
async def get_admin_announcements(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Lists all announcements."""
    announcements = AdminService.list_announcements()

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "announcements": announcements})
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/announcements.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "app_version": settings.APP_VERSION,
            "user": current_admin,
            "csrf_token": current_admin.get("csrf_token"),
            "announcements": announcements,
        },
    )


@admin_router.post("/announcements", summary="Create Announcement")
async def post_create_announcement(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Creates a new announcement."""
    data = await _extract_payload(request)
    admin_id = current_admin.get("user_id") or current_admin.get("id")
    try:
        created = AdminService.create_announcement(data, admin_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Duyuru yayınlandı.", "announcement": created})
        )

    return RedirectResponse(
        url="/admin/announcements?success=Duyuru+başarıyla+yayınlandı.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/announcements/{ann_id}/edit", summary="Update Announcement")
async def post_update_announcement(
    request: Request,
    ann_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Updates an announcement."""
    data = await _extract_payload(request)
    try:
        updated = AdminService.update_announcement(ann_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Duyuru güncellendi.", "announcement": updated})
        )

    return RedirectResponse(
        url="/admin/announcements?success=Duyuru+başarıyla+güncellendi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@admin_router.post("/announcements/{ann_id}/delete", summary="Delete Announcement")
async def post_delete_announcement(
    request: Request,
    ann_id: int,
    current_admin: Dict[str, Any] = Depends(require_role("admin")),
):
    """Deletes an announcement."""
    try:
        AdminService.delete_announcement(ann_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if _is_json_requested(request):
        return JSONResponse(
            jsonable_encoder({"status": "success", "message": "Duyuru silindi."})
        )

    return RedirectResponse(
        url="/admin/announcements?success=Duyuru+başarıyla+silindi.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
