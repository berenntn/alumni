"""REST API Announcement controller coordinating API requests and service layer operations."""

from typing import Any, Dict, Optional, Union
from app.models.announcement import Announcement
from app.services.announcement_service import AnnouncementService


class ApiAnnouncementController:
    """Controller responsible for REST API level announcement operations.

    Formats inputs and outputs for API consumers, delegating all domain
    and storage logic to AnnouncementService without maintaining internal state or
    database connections.
    """

    @classmethod
    def create_announcement(
        cls,
        announcement_or_data: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        id: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Creates an announcement via AnnouncementService and returns a REST API response.

        Args:
            announcement_or_data: Announcement instance, dictionary, or title string.
            content: Announcement content text.
            created_by: Creator user ID.
            title: Optional keyword argument for title.
            id: Optional explicit announcement ID.
            **kwargs: Additional announcement fields.

        Returns:
            Dictionary with API status, message, and serialized announcement data.
        """
        try:
            created_announcement = AnnouncementService.create_announcement(
                announcement_or_title=announcement_or_data,
                content=content,
                created_by=created_by,
                title=title,
                id=id,
                **kwargs,
            )
            return {
                "status": "success",
                "message": "Announcement created successfully",
                "data": created_announcement.model_dump(),
                "announcement": created_announcement,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "data": None,
                "announcement": None,
            }

    @classmethod
    def get_announcement(cls, announcement_id: int) -> Dict[str, Any]:
        """Retrieves a single announcement by ID via AnnouncementService for REST API response.

        Args:
            announcement_id: Unique identifier of the announcement.

        Returns:
            Dictionary with API status, message, and serialized announcement data (if found).
        """
        announcement = AnnouncementService.get_announcement(announcement_id)
        if announcement is None:
            return {
                "status": "error",
                "message": f"Announcement with id {announcement_id} not found",
                "data": None,
                "announcement": None,
            }
        return {
            "status": "success",
            "message": "Announcement retrieved successfully",
            "data": announcement.model_dump(),
            "announcement": announcement,
        }

    @classmethod
    def get_announcements(cls) -> Dict[str, Any]:
        """Retrieves all announcements via AnnouncementService for REST API response.

        Returns:
            Dictionary with API status, list of serialized announcements, and total count.
        """
        announcements = AnnouncementService.get_announcements()
        return {
            "status": "success",
            "message": f"Retrieved {len(announcements)} announcements",
            "data": [a.model_dump() for a in announcements],
            "announcements": announcements,
            "count": len(announcements),
        }

    @classmethod
    def update_announcement(
        cls,
        announcement_id: int,
        announcement_or_data: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Updates an announcement via AnnouncementService and returns a REST API response.

        Args:
            announcement_id: Unique identifier of the announcement to update.
            announcement_or_data: Announcement instance, dictionary, or updated title.
            content: Updated announcement content.
            created_by: Updated creator user ID.
            title: Optional keyword argument for updated title.
            **kwargs: Additional updated fields.

        Returns:
            Dictionary with API status, message, and serialized updated announcement data.
        """
        try:
            updated_announcement = AnnouncementService.update_announcement(
                announcement_id=announcement_id,
                announcement_or_title=announcement_or_data,
                content=content,
                created_by=created_by,
                title=title,
                **kwargs,
            )
            if updated_announcement is None:
                return {
                    "status": "error",
                    "message": f"Announcement with id {announcement_id} not found",
                    "data": None,
                    "announcement": None,
                }
            return {
                "status": "success",
                "message": "Announcement updated successfully",
                "data": updated_announcement.model_dump(),
                "announcement": updated_announcement,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "data": None,
                "announcement": None,
            }

    @classmethod
    def delete_announcement(cls, announcement_id: int) -> Dict[str, Any]:
        """Deletes an announcement by ID via AnnouncementService and returns a REST API response.

        Args:
            announcement_id: Unique identifier of the announcement to delete.

        Returns:
            Dictionary with API status and message.
        """
        deleted = AnnouncementService.delete_announcement(announcement_id)
        if not deleted:
            return {
                "status": "error",
                "message": f"Announcement with id {announcement_id} not found",
            }
        return {
            "status": "success",
            "message": f"Announcement {announcement_id} deleted successfully",
        }
