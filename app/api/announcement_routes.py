"""REST API routes for Announcement management coordinating with ApiAnnouncementController."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Response, status
from app.controllers.api_announcement_controller import ApiAnnouncementController
from app.core.dependencies import get_current_user
from app.schemas.announcement_schemas import (
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
    AnnouncementPatchRequest,
    AnnouncementApiResponse,
    AnnouncementListApiResponse,
    AnnouncementDeleteApiResponse,
)

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


def _check_announcement_permission(announcement_id: int, current_user: Dict[str, Any]):
    """Enforces that caller is either an admin or the author (academician)."""
    user_role = current_user.get("role")

    # Admin has unrestricted moderation access to all announcements
    if user_role == "admin":
        return

    # Ordinary users (alumni, students) cannot edit or delete announcements
    if user_role != "academician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu duyuruyu değiştirme veya silme yetkiniz bulunmamaktadır.",
        )

    # Academician: verify announcement exists and caller is the author
    res = ApiAnnouncementController.get_announcement(announcement_id)
    if res.get("status") != "success" or not res.get("data"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duyuru bulunamadı (ID: {announcement_id}).",
        )

    data = res["data"]
    author_id = data.created_by if hasattr(data, "created_by") else data.get("created_by")
    if author_id is None or author_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu duyuruyu değiştirme veya silme yetkiniz bulunmamaktadır.",
        )


@router.get(
    "",
    response_model=AnnouncementListApiResponse,
    summary="List All Announcements",
    description="Retrieves a list of all announcements stored in PostgreSQL via ApiAnnouncementController.",
)
@router.get(
    "/",
    response_model=AnnouncementListApiResponse,
    include_in_schema=False,
)
async def list_announcements():
    """Retrieves all announcements via ApiAnnouncementController."""
    return ApiAnnouncementController.get_announcements()


@router.post(
    "",
    response_model=AnnouncementApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Announcement",
    description="Creates a new announcement in PostgreSQL via ApiAnnouncementController.",
)
@router.post(
    "/",
    response_model=AnnouncementApiResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_announcement(
    payload: AnnouncementCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Creates a new announcement via ApiAnnouncementController (Admin or Academician only)."""
    user_role = current_user.get("role")
    if user_role not in ("admin", "academician"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Duyuru oluşturma yetkiniz bulunmamaktadır. Yalnızca yönetici veya akademisyenler duyuru yayınlayabilir.",
        )

    data = payload.model_dump()
    if user_role != "admin" or not data.get("created_by"):
        data["created_by"] = current_user.get("user_id")

    return ApiAnnouncementController.create_announcement(data)


@router.get(
    "/{id}",
    response_model=AnnouncementApiResponse,
    summary="Get Announcement by ID",
    description="Retrieves a specific announcement by its unique numeric ID via ApiAnnouncementController.",
)
async def get_announcement(
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the announcement", examples=[1]),
):
    """Retrieves an announcement by ID via ApiAnnouncementController."""
    result = ApiAnnouncementController.get_announcement(id)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.put(
    "/{id}",
    response_model=AnnouncementApiResponse,
    summary="Full Update Announcement",
    description="Completely updates all fields of an existing announcement via ApiAnnouncementController.",
)
async def update_announcement(
    payload: AnnouncementUpdateRequest,
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the announcement to update", examples=[1]),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Fully updates an announcement via ApiAnnouncementController (Author or Admin only)."""
    _check_announcement_permission(id, current_user)

    update_data = payload.model_dump()
    if current_user.get("role") != "admin":
        update_data.pop("created_by", None)

    result = ApiAnnouncementController.update_announcement(id, announcement_or_data=update_data)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.patch(
    "/{id}",
    response_model=AnnouncementApiResponse,
    summary="Partial Update Announcement",
    description="Partially updates specified fields of an existing announcement via ApiAnnouncementController.",
)
async def patch_announcement(
    payload: AnnouncementPatchRequest,
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the announcement to patch", examples=[1]),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Partially updates an announcement via ApiAnnouncementController (Author or Admin only)."""
    _check_announcement_permission(id, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    if current_user.get("role") != "admin":
        update_data.pop("created_by", None)

    result = ApiAnnouncementController.update_announcement(id, announcement_or_data=update_data)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.delete(
    "/{id}",
    response_model=AnnouncementDeleteApiResponse,
    summary="Delete Announcement",
    description="Deletes an existing announcement from PostgreSQL database via ApiAnnouncementController.",
)
async def delete_announcement(
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the announcement to delete", examples=[1]),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Deletes an announcement via ApiAnnouncementController (Author or Admin/Academician only)."""
    _check_announcement_permission(id, current_user)

    result = ApiAnnouncementController.delete_announcement(id)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result
