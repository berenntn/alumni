"""Announcement service providing database-backed CRUD operations using SQLAlchemy."""

import os
from typing import List, Optional, Union
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db_session, init_db
from app.models.announcement import Announcement, AnnouncementDB


class AnnouncementService:
    """Database-backed CRUD service for Announcement entities.

    Delegates all persistence operations to PostgreSQL via SQLAlchemy.
    Does not use in-memory dictionaries for persistence.
    """

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensures database tables are initialized before executing operations."""
        init_db()

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
        """Creates and stores a new Announcement in the database.

        Can be called with:
        - An Announcement instance: create_announcement(Announcement(...))
        - A dict: create_announcement({"title": "...", "content": "..."})
        - Positional or keyword arguments: create_announcement(title="...", content="...", ...)
        """
        cls._ensure_initialized()

        target_id: Optional[int] = id
        raw_title: Optional[str] = None
        raw_content: Optional[str] = None
        raw_created_by: Optional[int] = None

        if isinstance(announcement_or_title, Announcement):
            target_id = announcement_or_title.id if announcement_or_title.id is not None else target_id
            raw_title = announcement_or_title.title
            raw_content = announcement_or_title.content
            raw_created_by = announcement_or_title.created_by
        elif isinstance(announcement_or_title, dict):
            target_id = announcement_or_title.get("id") or target_id
            raw_title = announcement_or_title.get("title")
            raw_content = announcement_or_title.get("content")
            raw_created_by = announcement_or_title.get("created_by")
        else:
            raw_title = title if title is not None else (str(announcement_or_title) if announcement_or_title is not None else None)
            raw_content = content
            raw_created_by = created_by

        if not raw_title:
            raise ValueError("Announcement title must be provided.")

        # Validate through Pydantic model to enforce model constraints
        validated = Announcement(
            id=target_id,
            title=raw_title,
            content=raw_content,
            created_by=raw_created_by,
            **kwargs,
        )

        db_item = AnnouncementDB(
            title=validated.title,
            content=validated.content,
            created_by=validated.created_by,
        )
        if target_id is not None:
            db_item.id = target_id

        with get_db_session() as db:
            db.add(db_item)
            db.flush()
            db.refresh(db_item)
            return Announcement.model_validate(db_item)

    @classmethod
    def get_announcement(cls, announcement_id: int) -> Optional[Announcement]:
        """Retrieves a single announcement by ID from the database.

        Args:
            announcement_id: Unique identifier of the announcement.

        Returns:
            Announcement if found, None otherwise.
        """
        cls._ensure_initialized()
        with get_db_session() as db:
            record = (
                db.query(AnnouncementDB)
                .filter(AnnouncementDB.id == announcement_id)
                .first()
            )
            if record is None:
                return None
            return Announcement.model_validate(record)

    @classmethod
    def get_announcements(cls) -> List[Announcement]:
        """Retrieves all announcements currently stored in the database.

        Returns:
            List of all Announcement objects.
        """
        cls._ensure_initialized()
        with get_db_session() as db:
            records = (
                db.query(AnnouncementDB)
                .order_by(AnnouncementDB.id.asc())
                .all()
            )
            return [Announcement.model_validate(r) for r in records]

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
        """Updates an existing announcement in the database.

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
        cls._ensure_initialized()
        with get_db_session() as db:
            record = (
                db.query(AnnouncementDB)
                .filter(AnnouncementDB.id == announcement_id)
                .first()
            )
            if record is None:
                return None

            updates: dict = {}
            if isinstance(announcement_or_title, Announcement):
                updates = announcement_or_title.model_dump(
                    exclude_unset=True, exclude={"id"}
                )
            elif isinstance(announcement_or_title, dict):
                updates = {
                    k: v
                    for k, v in announcement_or_title.items()
                    if k != "id" and v is not None
                }
            else:
                resolved_title = (
                    title if title is not None else announcement_or_title
                )
                if resolved_title is not None:
                    updates["title"] = resolved_title
                if content is not None:
                    updates["content"] = content
                if created_by is not None:
                    updates["created_by"] = created_by
                for k, v in kwargs.items():
                    if k != "id" and v is not None:
                        updates[k] = v

            existing_dict = Announcement.model_validate(record).model_dump()
            existing_dict.update(updates)

            # Validate merged data using Pydantic model
            validated = Announcement(**existing_dict)

            record.title = validated.title
            record.content = validated.content
            record.created_by = validated.created_by

            db.flush()
            db.refresh(record)
            return Announcement.model_validate(record)

    @classmethod
    def delete_announcement(cls, announcement_id: int) -> bool:
        """Deletes an announcement from the database by ID.

        Args:
            announcement_id: Unique identifier of the announcement to delete.

        Returns:
            True if announcement was found and deleted, False otherwise.
        """
        cls._ensure_initialized()
        with get_db_session() as db:
            record = (
                db.query(AnnouncementDB)
                .filter(AnnouncementDB.id == announcement_id)
                .first()
            )
            if record is None:
                return False
            db.delete(record)
            return True

    @classmethod
    def clear_announcements(cls) -> None:
        """Clears all announcements in isolated test environments.

        Guards against accidental deletion of persistent PostgreSQL production data.
        """
        cls._ensure_initialized()
        from app.core.database import get_engine
        dialect_name = get_engine().dialect.name
        if dialect_name != "sqlite":
            is_test_env = (
                settings.APP_ENV == "test"
                or os.environ.get("TESTING", "").lower() in ("true", "1")
            )
            if not is_test_env:
                # Protection: Do not wipe persistent PostgreSQL database
                return

        with get_db_session() as db:

            db.query(AnnouncementDB).delete()
            if dialect_name == "sqlite":
                try:
                    db.execute(text("DELETE FROM sqlite_sequence WHERE name='announcements'"))
                except Exception:
                    pass
            elif dialect_name == "postgresql":
                try:
                    db.execute(text("ALTER SEQUENCE announcements_id_seq RESTART WITH 1"))
                except Exception:
                    pass


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
