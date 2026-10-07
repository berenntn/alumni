"""Web-facing User controller coordinating between presentation and service layers."""

from typing import Any, Dict, Optional, Union
from app.models.user import User
from app.services.user_service import UserService


class UserController:
    """Controller responsible for general and web-facing user operations.

    Delegates all domain and persistence logic to UserService without
    maintaining internal storage or database connections.
    """

    @classmethod
    def create_user(
        cls,
        user_or_name: Optional[Union[User, dict, str]] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        graduation_year: Optional[int] = None,
        *,
        name: Optional[str] = None,
        id: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Handles user creation for web presentation workflows.

        Args:
            user_or_name: User instance, dictionary of fields, or name string.
            email: User email address.
            department: User department.
            graduation_year: Year of graduation.
            name: Optional keyword argument for name.
            id: Optional explicit user ID.
            **kwargs: Additional user fields.

        Returns:
            Dictionary containing success status, message, and created user.
        """
        try:
            created_user = UserService.create_user(
                user_or_name=user_or_name,
                email=email,
                department=department,
                graduation_year=graduation_year,
                name=name,
                id=id,
                **kwargs,
            )
            return {
                "success": True,
                "message": "User created successfully",
                "user": created_user,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": str(exc),
                "user": None,
            }

    @classmethod
    def get_user(cls, user_id: int) -> Dict[str, Any]:
        """Retrieves a single user by ID for web presentation.

        Args:
            user_id: Unique identifier of the user.

        Returns:
            Dictionary containing success status, user object (if found), and message.
        """
        user = UserService.get_user(user_id)
        if user is None:
            return {
                "success": False,
                "message": f"User with id {user_id} not found",
                "user": None,
            }
        return {
            "success": True,
            "message": "User retrieved successfully",
            "user": user,
        }

    @classmethod
    def get_users(cls) -> Dict[str, Any]:
        """Retrieves all users for web presentation.

        Returns:
            Dictionary containing success status, list of users, and total count.
        """
        users = UserService.get_users()
        return {
            "success": True,
            "message": f"Retrieved {len(users)} users",
            "users": users,
            "count": len(users),
        }

    @classmethod
    def update_user(
        cls,
        user_id: int,
        user_or_name: Optional[Union[User, dict, str]] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        graduation_year: Optional[int] = None,
        *,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Updates an existing user's data for web presentation.

        Args:
            user_id: Unique identifier of the user to update.
            user_or_name: User instance, dictionary of fields, or updated name.
            email: Updated email address.
            department: Updated department.
            graduation_year: Updated graduation year.
            name: Optional keyword argument for updated name.
            **kwargs: Additional updated fields.

        Returns:
            Dictionary containing success status, message, and updated user.
        """
        try:
            updated_user = UserService.update_user(
                user_id=user_id,
                user_or_name=user_or_name,
                email=email,
                department=department,
                graduation_year=graduation_year,
                name=name,
                **kwargs,
            )
            if updated_user is None:
                return {
                    "success": False,
                    "message": f"User with id {user_id} not found",
                    "user": None,
                }
            return {
                "success": True,
                "message": "User updated successfully",
                "user": updated_user,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": str(exc),
                "user": None,
            }

    @classmethod
    def delete_user(cls, user_id: int) -> Dict[str, Any]:
        """Deletes a user by ID for web presentation.

        Args:
            user_id: Unique identifier of the user to delete.

        Returns:
            Dictionary containing success status and message.
        """
        deleted = UserService.delete_user(user_id)
        if not deleted:
            return {
                "success": False,
                "message": f"User with id {user_id} not found",
            }
        return {
            "success": True,
            "message": f"User {user_id} deleted successfully",
        }
