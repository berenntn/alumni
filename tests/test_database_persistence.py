"""Tests verifying database persistence and error propagation without in-memory fallbacks."""

import unittest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError

from app.models.announcement import Announcement, AnnouncementDB
from app.services.announcement_service import (
    AnnouncementService,
    clear_announcements,
    create_announcement,
    get_announcement,
)
from app.core.database import get_db_session


class TestDatabasePersistence(unittest.TestCase):
    """Test suite verifying Announcement persistence in database and error handling."""

    def setUp(self):
        clear_announcements()

    def tearDown(self):
        clear_announcements()

    def test_persistence_with_null_created_by(self):
        """Test creating an announcement with created_by=None and dynamically retrieving ID."""
        # Condition 1: created_by is None / null
        created = create_announcement(
            title="The Forgetting Test Duyurusu",
            content="PostgreSQL kalıcılık ve volume testi için oluşturuldu.",
            created_by=None,
        )

        # Condition 2: Retrieve real dynamic ID, do not assume 1
        real_id = created.id
        self.assertIsNotNone(real_id)
        self.assertIsNone(created.created_by)

        # Verify record exists in database table
        with get_db_session() as db:
            db_record = db.query(AnnouncementDB).filter(AnnouncementDB.id == real_id).first()
            self.assertIsNotNone(db_record)
            self.assertEqual(db_record.id, real_id)
            self.assertEqual(db_record.title, "The Forgetting Test Duyurusu")
            self.assertIsNone(db_record.created_by)

        # Verify retrieval via service
        retrieved = get_announcement(real_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, real_id)
        self.assertEqual(retrieved.title, "The Forgetting Test Duyurusu")
        self.assertIsNone(retrieved.created_by)

    def test_database_error_is_not_hidden(self):
        """Test that database connection errors propagate and are NOT hidden by falling back to RAM."""
        with patch("app.services.announcement_service.get_db_session") as mock_session:
            mock_session.side_effect = OperationalError("connection failure", params=None, orig=Exception("DB down"))
            with self.assertRaises(OperationalError):
                create_announcement(
                    title="Bu Duyuru Başarısız Olmalı",
                    content="Veritabanı kapalıyken RAM'e geçilmemeli.",
                )

    def test_production_guard_on_clear_announcements(self):
        """Test that clear_announcements guards against clearing if not in test environment."""
        created = create_announcement("Kalıcı Duyuru", "Silinmemesi gereken içerik")
        ann_id = created.id

        with patch("app.core.config.settings.APP_ENV", "production"):
            with patch.dict("os.environ", {"TESTING": "false"}):
                with patch("app.core.database.get_engine") as mock_get_engine:
                    mock_get_engine.return_value.dialect.name = "postgresql"
                    clear_announcements()

        # The announcement must NOT have been cleared
        still_there = get_announcement(ann_id)
        self.assertIsNotNone(still_there)


if __name__ == "__main__":
    unittest.main()
