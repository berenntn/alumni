"""REST API User controller coordinating API requests and service layer operations."""

from typing import Any, Dict, Optional, Union
from app.models.user import User
from app.services.user_service import UserService


class ApiUserController:
    """Controller responsible for REST API level user operations.

    Formats inputs and outputs for API consumers, delegating all domain
    and storage logic to UserService without maintaining internal state or
    database connections.
    """

    @classmethod
    def create_user(
        cls,
        user_or_data: Optional[Union[User, dict, str]] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        graduation_year: Optional[int] = None,
        *,
        name: Optional[str] = None,
        id: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Creates a user via UserService and returns a REST API response.

        Args:
            user_or_data: User instance, dictionary, or name string.
            email: User email address.
            department: User department.
            graduation_year: Year of graduation.
            name: Optional keyword argument for name.
            id: Optional explicit user ID.
            **kwargs: Additional user fields.

        Returns:
            Dictionary with API status, message, and serialized user data.
        """
        try:
            created_user = UserService.create_user(
                user_or_name=user_or_data,
                email=email,
                department=department,
                graduation_year=graduation_year,
                name=name,
                id=id,
                **kwargs,
            )
            return {
                "status": "success",
                "message": "User created successfully",
                "data": created_user.model_dump(),
                "user": created_user,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "data": None,
                "user": None,
            }

    @classmethod
    def get_user(cls, user_id: int) -> Dict[str, Any]:
        """Retrieves a single user by ID via UserService for REST API response.

        Args:
            user_id: Unique identifier of the user.

        Returns:
            Dictionary with API status, message, and serialized user data (if found).
        """
        user = UserService.get_user(user_id)
        if user is None:
            return {
                "status": "error",
                "message": f"User with id {user_id} not found",
                "data": None,
                "user": None,
            }
        return {
            "status": "success",
            "message": "User retrieved successfully",
            "data": user.model_dump(),
            "user": user,
        }

    @classmethod
    def get_users(cls) -> Dict[str, Any]:
        """Retrieves all users via UserService for REST API response.

        Returns:
            Dictionary with API status, list of serialized users, and total count.
        """
        users = UserService.get_users()
        return {
            "status": "success",
            "message": f"Retrieved {len(users)} users",
            "data": [u.model_dump() for u in users],
            "users": users,
            "count": len(users),
        }

    @classmethod
    def update_user(
        cls,
        user_id: int,
        user_or_data: Optional[Union[User, dict, str]] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        graduation_year: Optional[int] = None,
        *,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Updates a user via UserService and returns a REST API response.

        Args:
            user_id: Unique identifier of the user to update.
            user_or_data: User instance, dictionary, or updated name.
            email: Updated email address.
            department: Updated department.
            graduation_year: Updated graduation year.
            name: Optional keyword argument for updated name.
            **kwargs: Additional updated fields.

        Returns:
            Dictionary with API status, message, and serialized updated user data.
        """
        try:
            updated_user = UserService.update_user(
                user_id=user_id,
                user_or_name=user_or_data,
                email=email,
                department=department,
                graduation_year=graduation_year,
                name=name,
                **kwargs,
            )
            if updated_user is None:
                return {
                    "status": "error",
                    "message": f"User with id {user_id} not found",
                    "data": None,
                    "user": None,
                }
            return {
                "status": "success",
                "message": "User updated successfully",
                "data": updated_user.model_dump(),
                "user": updated_user,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "data": None,
                "user": None,
            }

    @classmethod
    def delete_user(cls, user_id: int) -> Dict[str, Any]:
        """Deletes a user by ID via UserService and returns a REST API response.

        Args:
            user_id: Unique identifier of the user to delete.

        Returns:
            Dictionary with API status and message.
        """
        deleted = UserService.delete_user(user_id)
        if not deleted:
            return {
                "status": "error",
                "message": f"User with id {user_id} not found",
            }
        return {
            "status": "success",
            "message": f"User {user_id} deleted successfully",
        }
