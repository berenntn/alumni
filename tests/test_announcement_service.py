"""Unit tests for AnnouncementService in-memory CRUD operations."""

import unittest

from app.models.announcement import Announcement
from app.services.announcement_service import (
    AnnouncementService,
    clear_announcements,
    create_announcement,
    delete_announcement,
    get_announcement,
    get_announcements,
    update_announcement,
)


class TestAnnouncementService(unittest.TestCase):
    """Test suite verifying in-memory AnnouncementService CRUD functionality."""

    def setUp(self):
        """Reset the in-memory announcement store before each test."""
        clear_announcements()

    def tearDown(self):
        """Clean up in-memory announcement store after each test."""
        clear_announcements()

    def test_create_announcement_with_args(self):
        """Test creating an announcement with individual arguments."""
        announcement = create_announcement(
            title="Mezunlar Günü 2026",
            content="Geleneksel mezunlar günü 15 Mayıs'ta yapılacaktır.",
            created_by=5,
        )
        self.assertEqual(announcement.id, 1)
        self.assertEqual(announcement.title, "Mezunlar Günü 2026")
        self.assertEqual(
            announcement.content,
            "Geleneksel mezunlar günü 15 Mayıs'ta yapılacaktır.",
        )
        self.assertEqual(announcement.created_by, 5)

    def test_create_announcement_with_dict(self):
        """Test creating an announcement by passing a dictionary."""
        data = {
            "title": "Kariyer Fuarı",
            "content": "Kariyer fuarı ana kampüste düzenlenecektir.",
            "created_by": 2,
        }
        announcement = create_announcement(data)
        self.assertEqual(announcement.id, 1)
        self.assertEqual(announcement.title, "Kariyer Fuarı")
        self.assertEqual(announcement.created_by, 2)

    def test_create_announcement_with_model(self):
        """Test creating an announcement by passing an Announcement model instance."""
        model_instance = Announcement(
            title="Burs Başvuruları",
            content="Burs başvuruları başlamıştır.",
            created_by=1,
        )
        announcement = create_announcement(model_instance)
        self.assertEqual(announcement.id, 1)
        self.assertEqual(announcement.title, "Burs Başvuruları")
        self.assertEqual(announcement.content, "Burs başvuruları başlamıştır.")
        self.assertEqual(announcement.created_by, 1)

    def test_create_multiple_announcements_auto_increment(self):
        """Test that announcement IDs auto-increment sequentially."""
        a1 = create_announcement("Duyuru 1", "İçerik 1")
        a2 = create_announcement("Duyuru 2", "İçerik 2")
        a3 = create_announcement("Duyuru 3", "İçerik 3")

        self.assertEqual(a1.id, 1)
        self.assertEqual(a2.id, 2)
        self.assertEqual(a3.id, 3)

    def test_create_announcement_missing_title(self):
        """Test creating an announcement without title raises ValueError."""
        with self.assertRaises(ValueError):
            create_announcement(title=None, content="İçerik")

    def test_get_announcement(self):
        """Test retrieving an announcement by ID."""
        created = create_announcement("Seminer", "Yapay zeka semineri", created_by=3)
        retrieved = get_announcement(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, created.id)
        self.assertEqual(retrieved.title, "Seminer")

        # Non-existent ID returns None
        self.assertIsNone(get_announcement(999))

    def test_get_announcements(self):
        """Test retrieving all announcements from memory."""
        self.assertEqual(len(get_announcements()), 0)

        create_announcement("Duyuru A", "İçerik A")
        create_announcement("Duyuru B", "İçerik B")

        all_announcements = get_announcements()
        self.assertEqual(len(all_announcements), 2)
        titles = [a.title for a in all_announcements]
        self.assertIn("Duyuru A", titles)
        self.assertIn("Duyuru B", titles)

    def test_update_announcement(self):
        """Test updating an existing announcement."""
        created = create_announcement("Eski Başlık", "Eski İçerik", created_by=1)

        # Partial update: change content
        updated = update_announcement(created.id, content="Yeni Güncel İçerik")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.content, "Yeni Güncel İçerik")
        self.assertEqual(updated.title, "Eski Başlık")  # Unchanged
        self.assertEqual(updated.created_by, 1)  # Unchanged

        # Update with dict
        updated_dict = update_announcement(created.id, {"title": "Yeni Başlık"})
        self.assertEqual(updated_dict.title, "Yeni Başlık")

        # Update non-existent announcement
        non_existent = update_announcement(999, title="Hayalet Duyuru")
        self.assertIsNone(non_existent)

    def test_delete_announcement(self):
        """Test deleting an announcement by ID."""
        created = create_announcement("Silinecek", "İçerik", created_by=1)
        self.assertEqual(len(get_announcements()), 1)

        # Successful deletion
        deleted = delete_announcement(created.id)
        self.assertTrue(deleted)
        self.assertEqual(len(get_announcements()), 0)
        self.assertIsNone(get_announcement(created.id))

        # Deleting non-existent announcement returns False
        self.assertFalse(delete_announcement(created.id))


if __name__ == "__main__":
    unittest.main()
