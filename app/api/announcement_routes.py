"""REST API routes for Announcement management coordinating with ApiAnnouncementController."""

from fastapi import APIRouter, Path as PathParam, Response, status
from app.controllers.api_announcement_controller import ApiAnnouncementController
from app.schemas.announcement_schemas import (
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
    AnnouncementPatchRequest,
    AnnouncementApiResponse,
    AnnouncementListApiResponse,
    AnnouncementDeleteApiResponse,
)

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


@router.get(
    "",
    response_model=AnnouncementListApiResponse,
    summary="List All Announcements",
    description="Retrieves a list of all announcements stored in memory via ApiAnnouncementController.",
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
    description="Creates a new announcement in memory via ApiAnnouncementController.",
)
@router.post(
    "/",
    response_model=AnnouncementApiResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_announcement(payload: AnnouncementCreateRequest):
    """Creates a new announcement via ApiAnnouncementController."""
    return ApiAnnouncementController.create_announcement(payload.model_dump())


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
):
    """Fully updates an announcement via ApiAnnouncementController."""
    result = ApiAnnouncementController.update_announcement(id, announcement_or_data=payload.model_dump())
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
):
    """Partially updates an announcement via ApiAnnouncementController."""
    result = ApiAnnouncementController.update_announcement(id, announcement_or_data=payload.model_dump(exclude_unset=True))
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.delete(
    "/{id}",
    response_model=AnnouncementDeleteApiResponse,
    summary="Delete Announcement",
    description="Deletes an existing announcement from in-memory storage via ApiAnnouncementController.",
)
async def delete_announcement(
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the announcement to delete", examples=[1]),
):
    """Deletes an announcement via ApiAnnouncementController."""
    result = ApiAnnouncementController.delete_announcement(id)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result
