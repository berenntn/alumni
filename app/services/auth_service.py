"""Authentication service handling user login, credential verification, and session creation."""

from typing import Any, Dict, Tuple
from pydantic import ValidationError
from sqlalchemy import func

from app.core.database import get_db_session
from app.core.security import verify_password
from app.models.user_db import UserDB
from app.schemas.login_schemas import UserLoginRequest
from app.services.session_service import SessionService


class AuthService:
    """Service providing credential verification and session generation for alumni users."""

    @classmethod
    def authenticate_user(
        cls,
        email: str,
        password: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Authenticates user credentials against PostgreSQL UserDB.

        Args:
            email: User email address.
            password: User plaintext candidate password.

        Returns:
            Tuple of (signed_session_token, safe_user_dict).

        Raises:
            ValueError: If validation fails or credentials are invalid.
        """
        # Validate email and password structure
        try:
            validated = UserLoginRequest(email=email, password=password)
        except ValidationError as e:
            first_err = e.errors()[0]
            msg = first_err.get("msg", "Lütfen geçerli e-posta ve şifrenizi giriniz.")
            if "Value error, " in msg:
                msg = msg.replace("Value error, ", "")
            raise ValueError(msg) from e

        normalized_email = validated.email.strip().lower()

        # Query user in PostgreSQL
        with get_db_session() as db:
            user = (
                db.query(UserDB)
                .filter(func.lower(UserDB.email) == normalized_email)
                .first()
            )

            # Security: Generic error message to prevent account enumeration
            if user is None or not user.hashed_password:
                raise ValueError("E-posta adresi veya şifre hatalı.")

            # Verify password using PBKDF2-HMAC-SHA256
            if not verify_password(validated.password, user.hashed_password):
                raise ValueError("E-posta adresi veya şifre hatalı.")

            # Extract user attributes while session is open
            # Note: Role is loaded strictly from the database
            user_data = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "graduation_year": user.graduation_year,
                "role": user.role or "alumnus",
            }

        # Create authenticated session token
        session_token = SessionService.create_session(user_data)
        session = SessionService.get_session(session_token)
        if session and "csrf_token" in session:
            user_data["csrf_token"] = session["csrf_token"]

        return session_token, user_data


authenticate_user = AuthService.authenticate_user

__all__ = [
    "AuthService",
    "authenticate_user",
]
