"""Web-facing Announcement controller coordinating between presentation and service layers."""

from typing import Any, Dict, Optional, Union
from app.models.announcement import Announcement
from app.services.announcement_service import AnnouncementService


class AnnouncementController:
    """Controller responsible for general and web-facing announcement operations.

    Delegates all domain and persistence logic to AnnouncementService without
    maintaining internal storage or database connections.
    """

    @classmethod
    def create_announcement(
        cls,
        announcement_or_title: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        id: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Handles announcement creation for web presentation workflows.

        Args:
            announcement_or_title: Announcement instance, dictionary of fields, or title string.
            content: Announcement content text.
            created_by: Creator user ID.
            title: Optional keyword argument for title.
            id: Optional explicit announcement ID.
            **kwargs: Additional announcement fields.

        Returns:
            Dictionary containing success status, message, and created announcement.
        """
        try:
            created_announcement = AnnouncementService.create_announcement(
                announcement_or_title=announcement_or_title,
                content=content,
                created_by=created_by,
                title=title,
                id=id,
                **kwargs,
            )
            return {
                "success": True,
                "message": "Announcement created successfully",
                "announcement": created_announcement,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": str(exc),
                "announcement": None,
            }

    @classmethod
    def get_announcement(cls, announcement_id: int) -> Dict[str, Any]:
        """Retrieves a single announcement by ID for web presentation.

        Args:
            announcement_id: Unique identifier of the announcement.

        Returns:
            Dictionary containing success status, announcement object (if found), and message.
        """
        announcement = AnnouncementService.get_announcement(announcement_id)
        if announcement is None:
            return {
                "success": False,
                "message": f"Announcement with id {announcement_id} not found",
                "announcement": None,
            }
        return {
            "success": True,
            "message": "Announcement retrieved successfully",
            "announcement": announcement,
        }

    @classmethod
    def get_announcements(cls) -> Dict[str, Any]:
        """Retrieves all announcements for web presentation.

        Returns:
            Dictionary containing success status, list of announcements, and total count.
        """
        announcements = AnnouncementService.get_announcements()
        return {
            "success": True,
            "message": f"Retrieved {len(announcements)} announcements",
            "announcements": announcements,
            "count": len(announcements),
        }

    @classmethod
    def update_announcement(
        cls,
        announcement_id: int,
        announcement_or_title: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Updates an existing announcement's data for web presentation.

        Args:
            announcement_id: Unique identifier of the announcement to update.
            announcement_or_title: Announcement instance, dictionary of fields, or updated title.
            content: Updated announcement content.
            created_by: Updated creator user ID.
            title: Optional keyword argument for updated title.
            **kwargs: Additional updated fields.

        Returns:
            Dictionary containing success status, message, and updated announcement.
        """
        try:
            updated_announcement = AnnouncementService.update_announcement(
                announcement_id=announcement_id,
                announcement_or_title=announcement_or_title,
                content=content,
                created_by=created_by,
                title=title,
                **kwargs,
            )
            if updated_announcement is None:
                return {
                    "success": False,
                    "message": f"Announcement with id {announcement_id} not found",
                    "announcement": None,
                }
            return {
                "success": True,
                "message": "Announcement updated successfully",
                "announcement": updated_announcement,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": str(exc),
                "announcement": None,
            }

    @classmethod
    def delete_announcement(cls, announcement_id: int) -> Dict[str, Any]:
        """Deletes an announcement by ID for web presentation.

        Args:
            announcement_id: Unique identifier of the announcement to delete.

        Returns:
            Dictionary containing success status and message.
        """
        deleted = AnnouncementService.delete_announcement(announcement_id)
        if not deleted:
            return {
                "success": False,
                "message": f"Announcement with id {announcement_id} not found",
            }
        return {
            "success": True,
            "message": f"Announcement {announcement_id} deleted successfully",
        }
