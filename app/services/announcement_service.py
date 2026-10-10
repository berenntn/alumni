"""In-memory Announcement service providing CRUD operations without database connection."""

from typing import Dict, List, Optional, Union
from app.models.announcement import Announcement


class AnnouncementService:
    """In-memory CRUD service for Announcement entities.

    Stores announcements temporarily in memory using a simple Python dictionary.
    No database operations or connection dependencies are utilized.
    """

    _announcements: Dict[int, Announcement] = {}
    _next_id: int = 1

    @classmethod
    def create_announcement(
        cls,
        announcement_or_title: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        id: Optional[int] = None,
        **kwargs,
    ) -> Announcement:
        """Creates and stores a new Announcement in memory.

        Can be called with:
        - An Announcement instance: create_announcement(Announcement(...))
        - A dict: create_announcement({"title": "...", "content": "..."})
        - Positional or keyword arguments: create_announcement(title="...", content="...", ...)
        """
        # Case 1: announcement_or_title is an Announcement instance
        if isinstance(announcement_or_title, Announcement):
            assigned_id = announcement_or_title.id if announcement_or_title.id is not None else cls._next_id
            if announcement_or_title.id is None:
                cls._next_id += 1
            else:
                cls._next_id = max(cls._next_id, assigned_id + 1)
            new_announcement = announcement_or_title.model_copy(update={"id": assigned_id})
            cls._announcements[assigned_id] = new_announcement
            return new_announcement

        # Case 2: announcement_or_title is a dictionary
        if isinstance(announcement_or_title, dict):
            data = dict(announcement_or_title)
            assigned_id = data.get("id") or id or cls._next_id
            if data.get("id") is None and id is None:
                cls._next_id += 1
            else:
                cls._next_id = max(cls._next_id, assigned_id + 1)
            data["id"] = assigned_id
            new_announcement = Announcement(**data)
            cls._announcements[assigned_id] = new_announcement
            return new_announcement

        # Case 3: Arguments provided via positional/keyword parameters
        resolved_title = title if title is not None else announcement_or_title
        if resolved_title is None:
            raise ValueError("Announcement title must be provided.")

        assigned_id = id if id is not None else cls._next_id
        if id is None:
            cls._next_id += 1
        else:
            cls._next_id = max(cls._next_id, assigned_id + 1)

        new_announcement = Announcement(
            id=assigned_id,
            title=str(resolved_title),
            content=content,
            created_by=created_by,
            **kwargs,
        )
        cls._announcements[assigned_id] = new_announcement
        return new_announcement

    @classmethod
    def get_announcement(cls, announcement_id: int) -> Optional[Announcement]:
        """Retrieves a single announcement by ID from memory.

        Args:
            announcement_id: Unique identifier of the announcement.

        Returns:
            Announcement if found, None otherwise.
        """
        return cls._announcements.get(announcement_id)

    @classmethod
    def get_announcements(cls) -> List[Announcement]:
        """Retrieves all announcements currently stored in memory.

        Returns:
            List of all Announcement objects.
        """
        return list(cls._announcements.values())

    @classmethod
    def update_announcement(
        cls,
        announcement_id: int,
        announcement_or_title: Optional[Union[Announcement, dict, str]] = None,
        content: Optional[str] = None,
        created_by: Optional[int] = None,
        *,
        title: Optional[str] = None,
        **kwargs,
    ) -> Optional[Announcement]:
        """Updates an existing announcement in memory.

        Args:
            announcement_id: Unique identifier of the announcement to update.
            announcement_or_title: Announcement instance, dict of updates, or title string.
            content: Updated announcement content.
            created_by: Updated creator user ID.
            title: Optional keyword argument for updated title.
            **kwargs: Additional fields to update.

        Returns:
            Updated Announcement if found, None otherwise.
        """
        existing_announcement = cls._announcements.get(announcement_id)
        if existing_announcement is None:
            return None

        updates: dict = {}
        if isinstance(announcement_or_title, Announcement):
            updates = announcement_or_title.model_dump(exclude_unset=True, exclude={"id"})
        elif isinstance(announcement_or_title, dict):
            updates = {k: v for k, v in announcement_or_title.items() if k != "id" and v is not None}
        else:
            resolved_title = title if title is not None else announcement_or_title
            if resolved_title is not None:
                updates["title"] = resolved_title
            if content is not None:
                updates["content"] = content
            if created_by is not None:
                updates["created_by"] = created_by
            for k, v in kwargs.items():
                if k != "id" and v is not None:
                    updates[k] = v

        updated_data = existing_announcement.model_dump()
        updated_data.update(updates)
        updated_announcement = Announcement(**updated_data)
        cls._announcements[announcement_id] = updated_announcement
        return updated_announcement

    @classmethod
    def delete_announcement(cls, announcement_id: int) -> bool:
        """Deletes an announcement from memory by ID.

        Args:
            announcement_id: Unique identifier of the announcement to delete.

        Returns:
            True if announcement was found and deleted, False otherwise.
        """
        if announcement_id in cls._announcements:
            del cls._announcements[announcement_id]
            return True
        return False

    @classmethod
    def clear_announcements(cls) -> None:
        """Clears all announcements in memory and resets ID counter (primarily for testing)."""
        cls._announcements.clear()
        cls._next_id = 1


# Standalone function aliases for direct import and functional usage
create_announcement = AnnouncementService.create_announcement
get_announcement = AnnouncementService.get_announcement
get_announcements = AnnouncementService.get_announcements
update_announcement = AnnouncementService.update_announcement
delete_announcement = AnnouncementService.delete_announcement
clear_announcements = AnnouncementService.clear_announcements

__all__ = [
    "AnnouncementService",
    "create_announcement",
    "get_announcement",
    "get_announcements",
    "update_announcement",
    "delete_announcement",
    "clear_announcements",
]
