"""Unit tests for AnnouncementController CRUD operations without database dependencies."""

import unittest
from app.controllers.announcement_controller import AnnouncementController
from app.models.announcement import Announcement
from app.services.announcement_service import clear_announcements


class TestAnnouncementController(unittest.TestCase):
    """Test suite verifying AnnouncementController operations and delegation to AnnouncementService."""

    def setUp(self):
        """Reset the in-memory announcement store before each test."""
        clear_announcements()

    def tearDown(self):
        """Clean up in-memory announcement store after each test."""
        clear_announcements()

    def test_create_announcement(self):
        """Test creating an announcement via AnnouncementController."""
        res = AnnouncementController.create_announcement(
            title="Genel Kurul Toplantısı",
            content="Mezunlar derneği genel kurul toplantısı yapılacaktır.",
            created_by=1,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "Announcement created successfully")
        self.assertIsNotNone(res["announcement"])
        self.assertEqual(res["announcement"].title, "Genel Kurul Toplantısı")
        self.assertEqual(res["announcement"].id, 1)

    def test_create_announcement_with_model(self):
        """Test creating an announcement passing an Announcement model to AnnouncementController."""
        announcement = Announcement(
            title="Proje Yarışması",
            content="Mühendislik mezunları proje yarışması başvuruları açıldı.",
            created_by=2,
        )
        res = AnnouncementController.create_announcement(announcement)
        self.assertTrue(res["success"])
        self.assertEqual(res["announcement"].title, "Proje Yarışması")

    def test_create_announcement_validation_error(self):
        """Test creating an announcement with invalid empty title returns success=False."""
        res = AnnouncementController.create_announcement(
            title="",
            content="İçerik var fakat başlık boş",
        )
        self.assertFalse(res["success"])
        self.assertIsNone(res["announcement"])
        self.assertIsNotNone(res["message"])

    def test_get_announcement(self):
        """Test retrieving a single announcement by ID via AnnouncementController."""
        create_res = AnnouncementController.create_announcement(
            title="Staj İlanı",
            content="Teknoloji staj programı duyurusu.",
            created_by=3,
        )
        announcement_id = create_res["announcement"].id

        # Successfully retrieve announcement
        get_res = AnnouncementController.get_announcement(announcement_id)
        self.assertTrue(get_res["success"])
        self.assertEqual(get_res["announcement"].title, "Staj İlanı")

        # Non-existent announcement
        not_found_res = AnnouncementController.get_announcement(999)
        self.assertFalse(not_found_res["success"])
        self.assertIsNone(not_found_res["announcement"])
        self.assertIn("not found", not_found_res["message"])

    def test_get_announcements(self):
        """Test retrieving all announcements via AnnouncementController."""
        empty_res = AnnouncementController.get_announcements()
        self.assertTrue(empty_res["success"])
        self.assertEqual(empty_res["count"], 0)
        self.assertEqual(len(empty_res["announcements"]), 0)

        AnnouncementController.create_announcement("Duyuru 1", "İçerik 1")
        AnnouncementController.create_announcement("Duyuru 2", "İçerik 2")

        announcements_res = AnnouncementController.get_announcements()
        self.assertTrue(announcements_res["success"])
        self.assertEqual(announcements_res["count"], 2)
        self.assertEqual(len(announcements_res["announcements"]), 2)

    def test_update_announcement(self):
        """Test updating an existing announcement via AnnouncementController."""
        create_res = AnnouncementController.create_announcement(
            title="Eski Başlık",
            content="Eski içerik açıklaması.",
            created_by=1,
        )
        announcement_id = create_res["announcement"].id

        # Perform partial update
        update_res = AnnouncementController.update_announcement(
            announcement_id,
            content="Güncellenmiş içerik açıklaması.",
        )
        self.assertTrue(update_res["success"])
        self.assertEqual(update_res["announcement"].content, "Güncellenmiş içerik açıklaması.")
        self.assertEqual(update_res["announcement"].title, "Eski Başlık")

        # Update non-existent announcement
        not_found = AnnouncementController.update_announcement(999, title="Hayalet")
        self.assertFalse(not_found["success"])
        self.assertIsNone(not_found["announcement"])

        # Update with invalid empty title
        invalid_res = AnnouncementController.update_announcement(announcement_id, title="")
        self.assertFalse(invalid_res["success"])
        self.assertIsNone(invalid_res["announcement"])

    def test_delete_announcement(self):
        """Test deleting an announcement via AnnouncementController."""
        create_res = AnnouncementController.create_announcement(
            title="Silinecek Başlık",
            content="Silinecek içerik.",
            created_by=4,
        )
        announcement_id = create_res["announcement"].id

        # Delete existing announcement
        del_res = AnnouncementController.delete_announcement(announcement_id)
        self.assertTrue(del_res["success"])
        self.assertIn("deleted successfully", del_res["message"])

        # Subsequent get returns not found
        get_res = AnnouncementController.get_announcement(announcement_id)
        self.assertFalse(get_res["success"])

        # Delete non-existent announcement
        del_non_existent = AnnouncementController.delete_announcement(announcement_id)
        self.assertFalse(del_non_existent["success"])


if __name__ == "__main__":
    unittest.main()
