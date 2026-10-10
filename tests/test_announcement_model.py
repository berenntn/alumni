"""Unit tests for Announcement model."""

import unittest
from pydantic import ValidationError

from app.models.announcement import Announcement
from app.models import Announcement as ExportedAnnouncement


class TestAnnouncementModel(unittest.TestCase):
    """Test cases for the Announcement Pydantic model."""

    def test_package_export(self):
        """Test Announcement model is exported properly from app.models."""
        self.assertIs(Announcement, ExportedAnnouncement)

    def test_valid_announcement_creation_all_fields(self):
        """Test creating an announcement with all fields provided."""
        announcement = Announcement(
            id=1,
            title="Mezunlar Buluşması 2026",
            content="Geleneksel mezunlar buluşması 15 Mayıs'ta Rektörlük bahçesinde yapılacaktır.",
            created_by=10,
        )
        self.assertEqual(announcement.id, 1)
        self.assertEqual(announcement.title, "Mezunlar Buluşması 2026")
        self.assertEqual(
            announcement.content,
            "Geleneksel mezunlar buluşması 15 Mayıs'ta Rektörlük bahçesinde yapılacaktır.",
        )
        self.assertEqual(announcement.created_by, 10)

    def test_announcement_default_values(self):
        """Test default values for optional fields id and created_by."""
        announcement = Announcement(
            title="Kariyer Günleri Başlıyor",
            content="Tüm mezun ve öğrencilerimiz davetlidir.",
        )
        self.assertIsNone(announcement.id)
        self.assertIsNone(announcement.created_by)
        self.assertEqual(announcement.title, "Kariyer Günleri Başlıyor")
        self.assertEqual(announcement.content, "Tüm mezun ve öğrencilerimiz davetlidir.")

    def test_invalid_empty_title(self):
        """Test that an empty title string fails validation (min_length=1)."""
        with self.assertRaises(ValidationError):
            Announcement(
                title="",
                content="Geçerli içerik",
            )

    def test_invalid_empty_content(self):
        """Test that an empty content string fails validation (min_length=1)."""
        with self.assertRaises(ValidationError):
            Announcement(
                title="Geçerli Başlık",
                content="",
            )

    def test_missing_required_fields(self):
        """Test that missing title or content raises ValidationError."""
        # Missing content
        with self.assertRaises(ValidationError):
            Announcement(title="Sadece Başlık")

        # Missing title
        with self.assertRaises(ValidationError):
            Announcement(content="Sadece İçerik")


if __name__ == "__main__":
    unittest.main()
