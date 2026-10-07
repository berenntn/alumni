"""Unit tests for ApiUserController REST API CRUD operations without database dependencies."""

import unittest
from app.controllers.api_user_controller import ApiUserController
from app.models.user import User
from app.services.user_service import clear_users


class TestApiUserController(unittest.TestCase):
    """Test suite verifying ApiUserController operations and REST API response formatting."""

    def setUp(self):
        """Reset the in-memory user store before each test."""
        clear_users()

    def tearDown(self):
        """Clean up in-memory user store after each test."""
        clear_users()

    def test_create_user(self):
        """Test creating a user via ApiUserController returns REST API format."""
        res = ApiUserController.create_user(
            name="Cemre Polat",
            email="cemre@example.com",
            department="Psikoloji",
            graduation_year=2023,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["message"], "User created successfully")
        self.assertIsInstance(res["data"], dict)
        self.assertEqual(res["data"]["id"], 1)
        self.assertEqual(res["data"]["name"], "Cemre Polat")
        self.assertEqual(res["data"]["email"], "cemre@example.com")

    def test_create_user_with_model(self):
        """Test creating a user passing a User model instance to ApiUserController."""
        user = User(
            name="Kaan Güneş",
            email="kaan@example.com",
            department="Matematik",
            graduation_year=2022,
        )
        res = ApiUserController.create_user(user)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["data"]["name"], "Kaan Güneş")

    def test_get_user(self):
        """Test retrieving a single user by ID via ApiUserController."""
        create_res = ApiUserController.create_user(
            name="Damla Er",
            email="damla@example.com",
            department="Tarih",
            graduation_year=2021,
        )
        user_id = create_res["data"]["id"]

        # Successfully retrieve existing user
        get_res = ApiUserController.get_user(user_id)
        self.assertEqual(get_res["status"], "success")
        self.assertIsNotNone(get_res["data"])
        self.assertEqual(get_res["data"]["name"], "Damla Er")

        # Non-existent user
        not_found_res = ApiUserController.get_user(999)
        self.assertEqual(not_found_res["status"], "error")
        self.assertIsNone(not_found_res["data"])
        self.assertIn("not found", not_found_res["message"])

    def test_get_users(self):
        """Test retrieving all users via ApiUserController."""
        empty_res = ApiUserController.get_users()
        self.assertEqual(empty_res["status"], "success")
        self.assertEqual(empty_res["count"], 0)
        self.assertEqual(len(empty_res["data"]), 0)

        ApiUserController.create_user("User A", "a@test.com", "Fizik", 2020)
        ApiUserController.create_user("User B", "b@test.com", "Kimya", 2021)

        users_res = ApiUserController.get_users()
        self.assertEqual(users_res["status"], "success")
        self.assertEqual(users_res["count"], 2)
        self.assertEqual(len(users_res["data"]), 2)
        self.assertEqual(users_res["data"][0]["name"], "User A")
        self.assertEqual(users_res["data"][1]["name"], "User B")

    def test_update_user(self):
        """Test updating a user via ApiUserController."""
        create_res = ApiUserController.create_user(
            name="Ozan Mert",
            email="ozan@old.com",
            department="İktisat",
            graduation_year=2018,
        )
        user_id = create_res["data"]["id"]

        # Update specific fields
        update_res = ApiUserController.update_user(
            user_id,
            email="ozan@new.com",
            department="Finans",
        )
        self.assertEqual(update_res["status"], "success")
        self.assertEqual(update_res["data"]["email"], "ozan@new.com")
        self.assertEqual(update_res["data"]["department"], "Finans")
        self.assertEqual(update_res["data"]["name"], "Ozan Mert")  # Unchanged

        # Update non-existent user
        not_found = ApiUserController.update_user(999, name="Ghost")
        self.assertEqual(not_found["status"], "error")
        self.assertIsNone(not_found["data"])

    def test_delete_user(self):
        """Test deleting a user via ApiUserController."""
        create_res = ApiUserController.create_user(
            name="Gizem Kurt",
            email="gizem@example.com",
            department="Hukuk",
            graduation_year=2024,
        )
        user_id = create_res["data"]["id"]

        # Delete existing user
        del_res = ApiUserController.delete_user(user_id)
        self.assertEqual(del_res["status"], "success")
        self.assertIn("deleted successfully", del_res["message"])

        # Subsequent get returns error
        get_res = ApiUserController.get_user(user_id)
        self.assertEqual(get_res["status"], "error")
        self.assertIsNone(get_res["data"])

        # Delete non-existent user
        del_non_existent = ApiUserController.delete_user(user_id)
        self.assertEqual(del_non_existent["status"], "error")


if __name__ == "__main__":
    unittest.main()
