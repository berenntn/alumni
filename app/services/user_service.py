"""In-memory User service providing CRUD operations without database connection."""

from typing import Dict, List, Optional, Union
from app.models.user import User


class UserService:
    """In-memory CRUD service for User entities.

    Stores users temporarily in memory using a simple Python dictionary.
    No database operations or connection dependencies are utilized.
    """

    _users: Dict[int, User] = {}
    _next_id: int = 1

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
        **kwargs,
    ) -> User:
        """Creates and stores a new User in memory.

        Can be called with:
        - A User instance: create_user(User(...))
        - A dict: create_user({"name": "...", "email": ...})
        - Positional or keyword arguments: create_user(name="...", email="...", ...)
        """
        # Case 1: user_or_name is a User instance
        if isinstance(user_or_name, User):
            assigned_id = user_or_name.id if user_or_name.id is not None else cls._next_id
            if user_or_name.id is None:
                cls._next_id += 1
            else:
                cls._next_id = max(cls._next_id, assigned_id + 1)
            new_user = user_or_name.model_copy(update={"id": assigned_id})
            cls._users[assigned_id] = new_user
            return new_user

        # Case 2: user_or_name is a dictionary
        if isinstance(user_or_name, dict):
            data = dict(user_or_name)
            assigned_id = data.get("id") or id or cls._next_id
            if data.get("id") is None and id is None:
                cls._next_id += 1
            else:
                cls._next_id = max(cls._next_id, assigned_id + 1)
            data["id"] = assigned_id
            new_user = User(**data)
            cls._users[assigned_id] = new_user
            return new_user

        # Case 3: Arguments provided via positional/keyword parameters
        resolved_name = name if name is not None else user_or_name
        if resolved_name is None:
            raise ValueError("User name must be provided.")

        assigned_id = id if id is not None else cls._next_id
        if id is None:
            cls._next_id += 1
        else:
            cls._next_id = max(cls._next_id, assigned_id + 1)

        new_user = User(
            id=assigned_id,
            name=str(resolved_name),
            email=email,
            department=department,
            graduation_year=graduation_year,
            **kwargs,
        )
        cls._users[assigned_id] = new_user
        return new_user

    @classmethod
    def get_user(cls, user_id: int) -> Optional[User]:
        """Retrieves a single user by ID from memory.

        Args:
            user_id: Unique identifier of the user.

        Returns:
            User if found, None otherwise.
        """
        return cls._users.get(user_id)

    @classmethod
    def get_users(cls) -> List[User]:
        """Retrieves all users currently stored in memory.

        Returns:
            List of all User objects.
        """
        return list(cls._users.values())

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
        **kwargs,
    ) -> Optional[User]:
        """Updates an existing user in memory.

        Args:
            user_id: Unique identifier of the user to update.
            user_or_name: User instance, dict of updates, or name string.
            email: Updated email address.
            department: Updated department.
            graduation_year: Updated graduation year.
            name: Optional keyword argument for updated name.
            **kwargs: Additional fields to update.

        Returns:
            Updated User if found, None otherwise.
        """
        existing_user = cls._users.get(user_id)
        if existing_user is None:
            return None

        updates: dict = {}
        if isinstance(user_or_name, User):
            updates = user_or_name.model_dump(exclude_unset=True, exclude={"id"})
        elif isinstance(user_or_name, dict):
            updates = {k: v for k, v in user_or_name.items() if k != "id" and v is not None}
        else:
            resolved_name = name if name is not None else user_or_name
            if resolved_name is not None:
                updates["name"] = resolved_name
            if email is not None:
                updates["email"] = email
            if department is not None:
                updates["department"] = department
            if graduation_year is not None:
                updates["graduation_year"] = graduation_year
            for k, v in kwargs.items():
                if k != "id" and v is not None:
                    updates[k] = v

        updated_data = existing_user.model_dump()
        updated_data.update(updates)
        updated_user = User(**updated_data)
        cls._users[user_id] = updated_user
        return updated_user

    @classmethod
    def delete_user(cls, user_id: int) -> bool:
        """Deletes a user from memory by ID.

        Args:
            user_id: Unique identifier of the user to delete.

        Returns:
            True if user was found and deleted, False otherwise.
        """
        if user_id in cls._users:
            del cls._users[user_id]
            return True
        return False

    @classmethod
    def clear_users(cls) -> None:
        """Clears all users in memory and resets ID counter (primarily for testing)."""
        cls._users.clear()
        cls._next_id = 1


# Standalone function aliases for direct import and functional usage
create_user = UserService.create_user
get_user = UserService.get_user
get_users = UserService.get_users
update_user = UserService.update_user
delete_user = UserService.delete_user
clear_users = UserService.clear_users

__all__ = [
    "UserService",
    "create_user",
    "get_user",
    "get_users",
    "update_user",
    "delete_user",
    "clear_users",
]
