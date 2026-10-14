"""Seed sample announcements without deleting existing records."""

from app.core.database import get_db_session
from app.factories.announcement_factory import AnnouncementFactory
from app.models.announcement import AnnouncementDB


def seed_announcements():
    """Insert sample announcements if their titles do not already exist."""
    samples = AnnouncementFactory.create_batch(5)
    added = 0

    with get_db_session() as db:
        for sample in samples:
            existing = (
                db.query(AnnouncementDB)
                .filter(AnnouncementDB.title == sample.title)
                .first()
            )

            if existing is not None:
                continue

            db.add(
                AnnouncementDB(
                    title=sample.title,
                    content=sample.content,
                    created_by=sample.created_by,
                )
            )
            added += 1

    return added


if __name__ == "__main__":
    count = seed_announcements()
    print("{} yeni örnek duyuru eklendi.".format(count))
