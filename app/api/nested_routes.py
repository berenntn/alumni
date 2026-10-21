"""Nested API routes for user announcements."""

from fastapi import APIRouter, Path
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.announcement import AnnouncementDB

router = APIRouter(prefix="/api/users", tags=["Nested Routes"])


@router.get("/{user_id}/announcements")
def get_user_announcements(
    user_id: int = Path(..., ge=1),
):
    """List announcements created by a specific user."""
    with get_db_session() as session:
        announcements = session.execute(
            select(AnnouncementDB).where(
                AnnouncementDB.created_by == user_id
            )
        ).scalars().all()

        return [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "created_by": item.created_by,
            }
            for item in announcements
        ]
