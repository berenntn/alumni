"""Unit tests for User model and in-memory UserService without database."""

import unittest
from pydantic import ValidationError

from app.models.user import User
from app.services.user_service import (
    UserService,
    create_user,
    get_user,
    get_users,
    update_user,
    delete_user,
    clear_users,
)


class TestUserService(unittest.TestCase):
    """Test suite for in-memory UserService CRUD operations."""

    def setUp(self):
        """Clear the in-memory user store before each test."""
        clear_users()

    def tearDown(self):
        """Clean up in-memory user store after each test."""
        clear_users()

    def test_create_user_with_args(self):
        """Test creating a user with individual arguments."""
        user = create_user(
            name="Berkay Tuna",
            email="berkay@example.com",
            department="Bilgisayar Mühendisliği",
            graduation_year=2024,
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, "Berkay Tuna")
        self.assertEqual(user.email, "berkay@example.com")
        self.assertEqual(user.department, "Bilgisayar Mühendisliği")
        self.assertEqual(user.graduation_year, 2024)

    def test_create_user_with_model(self):
        """Test creating a user by passing a User model instance."""
        user_model = User(
            name="Ayşe Yılmaz",
            email="ayse@example.com",
            department="Hukuk",
            graduation_year=2022,
        )
        created = create_user(user_model)
        self.assertEqual(created.id, 1)
        self.assertEqual(created.name, "Ayşe Yılmaz")

    def test_create_user_with_dict(self):
        """Test creating a user by passing a dictionary."""
        data = {
            "name": "Mehmet Demir",
            "email": "mehmet@example.com",
            "department": "İktisat",
            "graduation_year": 2020,
        }
        created = create_user(data)
        self.assertEqual(created.id, 1)
        self.assertEqual(created.name, "Mehmet Demir")

    def test_create_multiple_users_auto_increment(self):
        """Test that user IDs auto-increment sequentially."""
        u1 = create_user("User One", "one@example.com", "CS", 2021)
        u2 = create_user("User Two", "two@example.com", "EE", 2022)
        u3 = create_user("User Three", "three@example.com", "ME", 2023)
        self.assertEqual(u1.id, 1)
        self.assertEqual(u2.id, 2)
        self.assertEqual(u3.id, 3)

    def test_get_user(self):
        """Test retrieving a user by ID."""
        created = create_user("Canan Dağ", "canan@example.com", "Tıp", 2019)
        fetched = get_user(created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Canan Dağ")

        # Test non-existent ID
        not_found = get_user(999)
        self.assertIsNone(not_found)

    def test_get_users(self):
        """Test retrieving all users from memory."""
        self.assertEqual(len(get_users()), 0)

        create_user("User 1", "u1@example.com", "Dep 1", 2020)
        create_user("User 2", "u2@example.com", "Dep 2", 2021)

        users = get_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].name, "User 1")
        self.assertEqual(users[1].name, "User 2")

    def test_update_user(self):
        """Test updating an existing user."""
        created = create_user("Ece Kaya", "ece@example.com", "Eczacılık", 2023)
        
        # Partial update: change email and graduation year
        updated = update_user(created.id, email="ece.kaya@alumni.edu", graduation_year=2024)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.email, "ece.kaya@alumni.edu")
        self.assertEqual(updated.graduation_year, 2024)
        self.assertEqual(updated.name, "Ece Kaya")  # Unchanged
        self.assertEqual(updated.department, "Eczacılık")  # Unchanged

        # Update non-existent user
        non_existent = update_user(999, name="Ghost")
        self.assertIsNone(non_existent)

    def test_delete_user(self):
        """Test deleting a user by ID."""
        created = create_user("Kerem Barış", "kerem@example.com", "Felsefe", 2018)
        self.assertEqual(len(get_users()), 1)

        # Successful deletion
        deleted = delete_user(created.id)
        self.assertTrue(deleted)
        self.assertEqual(len(get_users()), 0)
        self.assertIsNone(get_user(created.id))

        # Deleting non-existent user returns False
        self.assertFalse(delete_user(created.id))

    def test_user_validation_pydantic(self):
        """Test Pydantic validation on User model."""
        # Valid user
        user = User(
            name="Valid Name",
            email="valid@example.com",
            department="Valid Dep",
            graduation_year=2025,
        )
        self.assertEqual(user.name, "Valid Name")

        # Invalid graduation year (out of range)
        with self.assertRaises(ValidationError):
            User(
                name="Time Traveler",
                email="time@example.com",
                department="Physics",
                graduation_year=1800,
            )

        # Missing required field
        with self.assertRaises(ValidationError):
            User(name="No Email", department="History", graduation_year=2020)  # Missing email


if __name__ == "__main__":
    unittest.main()
