"""Unit tests for UserController CRUD operations without database dependencies."""

import unittest
from app.controllers.user_controller import UserController
from app.models.user import User
from app.services.user_service import clear_users, UserService


class TestUserController(unittest.TestCase):
    """Test suite verifying UserController operations and delegation to UserService."""

    def setUp(self):
        """Reset the in-memory user store before each test."""
        clear_users()

    def tearDown(self):
        """Clean up in-memory user store after each test."""
        clear_users()

    def test_create_user(self):
        """Test creating a user via UserController."""
        res = UserController.create_user(
            name="Zeynep Kaya",
            email="zeynep@example.com",
            department="Mimarlık",
            graduation_year=2021,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "User created successfully")
        self.assertIsNotNone(res["user"])
        self.assertEqual(res["user"].name, "Zeynep Kaya")
        self.assertEqual(res["user"].id, 1)

    def test_create_user_with_model(self):
        """Test creating a user passing a User model to UserController."""
        user = User(
            name="Murat Arslan",
            email="murat@example.com",
            department="İşletme",
            graduation_year=2023,
        )
        res = UserController.create_user(user)
        self.assertTrue(res["success"])
        self.assertEqual(res["user"].name, "Murat Arslan")

    def test_get_user(self):
        """Test retrieving a single user by ID via UserController."""
        create_res = UserController.create_user(
            name="Selin Yıldız",
            email="selin@example.com",
            department="Sosyoloji",
            graduation_year=2020,
        )
        user_id = create_res["user"].id

        # Successfully retrieve user
        get_res = UserController.get_user(user_id)
        self.assertTrue(get_res["success"])
        self.assertEqual(get_res["user"].name, "Selin Yıldız")

        # Non-existent user
        not_found_res = UserController.get_user(999)
        self.assertFalse(not_found_res["success"])
        self.assertIsNone(not_found_res["user"])
        self.assertIn("not found", not_found_res["message"])

    def test_get_users(self):
        """Test retrieving all users via UserController."""
        empty_res = UserController.get_users()
        self.assertTrue(empty_res["success"])
        self.assertEqual(empty_res["count"], 0)
        self.assertEqual(len(empty_res["users"]), 0)

        UserController.create_user("User 1", "u1@test.com", "Dep 1", 2020)
        UserController.create_user("User 2", "u2@test.com", "Dep 2", 2021)

        users_res = UserController.get_users()
        self.assertTrue(users_res["success"])
        self.assertEqual(users_res["count"], 2)
        self.assertEqual(len(users_res["users"]), 2)

    def test_update_user(self):
        """Test updating an existing user via UserController."""
        create_res = UserController.create_user(
            name="Burak Çelik",
            email="burak@old.com",
            department="Kimya",
            graduation_year=2019,
        )
        user_id = create_res["user"].id

        # Perform partial update
        update_res = UserController.update_user(
            user_id,
            email="burak@new.com",
            graduation_year=2020,
        )
        self.assertTrue(update_res["success"])
        self.assertEqual(update_res["user"].email, "burak@new.com")
        self.assertEqual(update_res["user"].graduation_year, 2020)
        self.assertEqual(update_res["user"].name, "Burak Çelik")

        # Update non-existent user
        not_found = UserController.update_user(999, name="Ghost")
        self.assertFalse(not_found["success"])
        self.assertIsNone(not_found["user"])

    def test_delete_user(self):
        """Test deleting a user via UserController."""
        create_res = UserController.create_user(
            name="Deniz Ak",
            email="deniz@example.com",
            department="Biyoloji",
            graduation_year=2022,
        )
        user_id = create_res["user"].id

        # Delete existing user
        del_res = UserController.delete_user(user_id)
        self.assertTrue(del_res["success"])
        self.assertIn("deleted successfully", del_res["message"])

        # Subsequent get returns not found
        get_res = UserController.get_user(user_id)
        self.assertFalse(get_res["success"])

        # Delete non-existent user
        del_non_existent = UserController.delete_user(user_id)
        self.assertFalse(del_non_existent["success"])


if __name__ == "__main__":
    unittest.main()
