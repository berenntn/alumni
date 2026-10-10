"""Unit tests for ApiAnnouncementController REST API CRUD operations without database dependencies."""

import unittest
from app.controllers.api_announcement_controller import ApiAnnouncementController
from app.models.announcement import Announcement
from app.services.announcement_service import clear_announcements


class TestApiAnnouncementController(unittest.TestCase):
    """Test suite verifying ApiAnnouncementController operations and REST API response formatting."""

    def setUp(self):
        """Reset the in-memory announcement store before each test."""
        clear_announcements()

    def tearDown(self):
        """Clean up in-memory announcement store after each test."""
        clear_announcements()

    def test_create_announcement(self):
        """Test creating an announcement via ApiAnnouncementController returns REST API format."""
        res = ApiAnnouncementController.create_announcement(
            title="Bahar Şenliği",
            content="Bahar şenliği 20-22 Mayıs tarihlerinde gerçekleştirilecektir.",
            created_by=10,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["message"], "Announcement created successfully")
        self.assertIsInstance(res["data"], dict)
        self.assertEqual(res["data"]["id"], 1)
        self.assertEqual(res["data"]["title"], "Bahar Şenliği")
        self.assertEqual(res["data"]["content"], "Bahar şenliği 20-22 Mayıs tarihlerinde gerçekleştirilecektir.")
        self.assertEqual(res["data"]["created_by"], 10)

    def test_create_announcement_with_model(self):
        """Test creating an announcement passing an Announcement model instance to ApiAnnouncementController."""
        announcement = Announcement(
            title="Akademik Takvim",
            content="Güz dönemi akademik takvimi güncellendi.",
            created_by=1,
        )
        res = ApiAnnouncementController.create_announcement(announcement)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["data"]["title"], "Akademik Takvim")

    def test_create_announcement_validation_error(self):
        """Test creating an announcement with empty title returns status='error'."""
        res = ApiAnnouncementController.create_announcement(
            title="",
            content="İçerik var ama başlık geçersiz.",
        )
        self.assertEqual(res["status"], "error")
        self.assertIsNone(res["data"])
        self.assertIsNotNone(res["message"])

    def test_get_announcement(self):
        """Test retrieving a single announcement by ID via ApiAnnouncementController."""
        create_res = ApiAnnouncementController.create_announcement(
            title="Mentorluk Programı",
            content="Mezun-öğrenci mentorluk programı eşleşmeleri başladı.",
            created_by=2,
        )
        announcement_id = create_res["data"]["id"]

        # Successfully retrieve existing announcement
        get_res = ApiAnnouncementController.get_announcement(announcement_id)
        self.assertEqual(get_res["status"], "success")
        self.assertIsNotNone(get_res["data"])
        self.assertEqual(get_res["data"]["title"], "Mentorluk Programı")

        # Non-existent announcement
        not_found_res = ApiAnnouncementController.get_announcement(999)
        self.assertEqual(not_found_res["status"], "error")
        self.assertIsNone(not_found_res["data"])
        self.assertIn("not found", not_found_res["message"])

    def test_get_announcements(self):
        """Test retrieving all announcements via ApiAnnouncementController."""
        empty_res = ApiAnnouncementController.get_announcements()
        self.assertEqual(empty_res["status"], "success")
        self.assertEqual(empty_res["count"], 0)
        self.assertEqual(len(empty_res["data"]), 0)

        ApiAnnouncementController.create_announcement("Duyuru A", "İçerik A")
        ApiAnnouncementController.create_announcement("Duyuru B", "İçerik B")

        announcements_res = ApiAnnouncementController.get_announcements()
        self.assertEqual(announcements_res["status"], "success")
        self.assertEqual(announcements_res["count"], 2)
        self.assertEqual(len(announcements_res["data"]), 2)
        self.assertEqual(announcements_res["data"][0]["title"], "Duyuru A")
        self.assertEqual(announcements_res["data"][1]["title"], "Duyuru B")

    def test_update_announcement(self):
        """Test updating an announcement via ApiAnnouncementController."""
        create_res = ApiAnnouncementController.create_announcement(
            title="Eski Başlık",
            content="Eski duyuru açıklaması.",
            created_by=3,
        )
        announcement_id = create_res["data"]["id"]

        # Update specific fields
        update_res = ApiAnnouncementController.update_announcement(
            announcement_id,
            content="Güncellenmiş duyuru açıklaması.",
        )
        self.assertEqual(update_res["status"], "success")
        self.assertEqual(update_res["data"]["content"], "Güncellenmiş duyuru açıklaması.")
        self.assertEqual(update_res["data"]["title"], "Eski Başlık")  # Unchanged
        self.assertEqual(update_res["data"]["created_by"], 3)  # Unchanged

        # Update non-existent announcement
        not_found = ApiAnnouncementController.update_announcement(999, title="Hayalet")
        self.assertEqual(not_found["status"], "error")
        self.assertIsNone(not_found["data"])

        # Update with invalid data
        invalid_res = ApiAnnouncementController.update_announcement(announcement_id, title="")
        self.assertEqual(invalid_res["status"], "error")
        self.assertIsNone(invalid_res["data"])

    def test_delete_announcement(self):
        """Test deleting an announcement via ApiAnnouncementController."""
        create_res = ApiAnnouncementController.create_announcement(
            title="Kaldırılacak Duyuru",
            content="Bu duyuru silinecektir.",
            created_by=5,
        )
        announcement_id = create_res["data"]["id"]

        # Delete existing announcement
        del_res = ApiAnnouncementController.delete_announcement(announcement_id)
        self.assertEqual(del_res["status"], "success")
        self.assertIn("deleted successfully", del_res["message"])

        # Subsequent get returns error
        get_res = ApiAnnouncementController.get_announcement(announcement_id)
        self.assertEqual(get_res["status"], "error")
        self.assertIsNone(get_res["data"])

        # Delete non-existent announcement
        del_non_existent = ApiAnnouncementController.delete_announcement(announcement_id)
        self.assertEqual(del_non_existent["status"], "error")


if __name__ == "__main__":
    unittest.main()
