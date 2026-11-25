"""Registration service for managing alumni user sign-ups.

Persists registered users to PostgreSQL via SQLAlchemy, hashes passwords securely,
enforces email uniqueness, assigns safe default roles, and mirrors records into
the in-memory UserService to preserve architecture consistency.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import ValidationError
from sqlalchemy import func

from app.core.database import get_db_session
from app.core.security import hash_password
from app.models.user_db import UserDB
from app.schemas.auth_schemas import UserRegisterRequest
from app.services.user_service import UserService


class RegistrationService:
    """Service handling alumni registration validation, hashing, and dual-layer persistence."""

    @classmethod
    def register_user(
        cls,
        payload_or_name: Optional[Union[UserRegisterRequest, dict, str]] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        graduation_year: Optional[int] = None,
        password: Optional[str] = None,
        confirm_password: Optional[str] = None,
        *,
        name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Registers a new alumnus user.

        Args:
            payload_or_name: UserRegisterRequest instance, dict, or full name string.
            email: Email address.
            department: Department name.
            graduation_year: Graduation year integer.
            password: Plaintext password (min 8 chars).
            confirm_password: Password confirmation.
            name: Optional keyword argument for full name.
            **kwargs: Extra parameters (safely filtered; roles are never accepted from clients).

        Returns:
            Dictionary containing public user details (id, name, email, department, graduation_year, role).

        Raises:
            ValueError: If input validation fails or email already exists.
        """
        # Step 1: Normalize input into dictionary
        data: Dict[str, Any] = {}
        if isinstance(payload_or_name, UserRegisterRequest):
            data = payload_or_name.model_dump()
        elif isinstance(payload_or_name, dict):
            data = dict(payload_or_name)
        else:
            resolved_name = name if name is not None else payload_or_name
            data = {
                "name": resolved_name,
                "email": email,
                "department": department,
                "graduation_year": graduation_year,
                "password": password,
                "confirm_password": confirm_password,
            }

        # Step 2: Validate fields using Pydantic schema
        try:
            validated = UserRegisterRequest(**data)
        except ValidationError as e:
            first_err = e.errors()[0]
            loc = first_err.get("loc", ())
            msg = first_err.get("msg", "Geçersiz giriş verisi.")
            field_name = loc[-1] if loc else ""

            if "at least 8" in msg or field_name == "password":
                msg = "Şifre en az 8 karakter olmalıdır."
            elif field_name == "graduation_year" and ("greater than or equal" in msg or "less than or equal" in msg):
                msg = "Mezuniyet yılı 1900 ile 2100 arasında olmalıdır."
            elif "Field required" in msg or "missing" in msg:
                field_tr = {
                    "name": "Tam Adı Soyadı",
                    "email": "E-posta",
                    "department": "Bölüm",
                    "graduation_year": "Mezuniyet Yılı",
                    "password": "Şifre",
                    "confirm_password": "Şifre Tekrarı",
                }.get(str(field_name), str(field_name))
                msg = f"{field_tr} alanı zorunludur."
            elif "Value error, " in msg:
                msg = msg.replace("Value error, ", "")

            raise ValueError(msg) from e

        normalized_email = validated.email.strip().lower()

        # Step 3: Check email uniqueness in PostgreSQL UserDB
        with get_db_session() as db:
            existing_db = (
                db.query(UserDB)
                .filter(func.lower(UserDB.email) == normalized_email)
                .first()
            )
            if existing_db is not None:
                raise ValueError("Bu e-posta adresi ile kayıtlı bir kullanıcı zaten mevcut.")

        # Step 4: Check email uniqueness in in-memory UserService
        for mem_user in UserService.get_users():
            if mem_user.email and mem_user.email.strip().lower() == normalized_email:
                raise ValueError("Bu e-posta adresi ile kayıtlı bir kullanıcı zaten mevcut.")

        # Step 5: Hash password securely
        hashed_pw = hash_password(validated.password)

        # Step 6: Create and persist UserDB record in PostgreSQL
        # Security: Force safe default role 'alumnus' on server side
        db_user = UserDB(
            name=validated.name,
            email=normalized_email,
            department=validated.department,
            graduation_year=validated.graduation_year,
            hashed_password=hashed_pw,
            role="alumnus",
            created_at=datetime.utcnow(),
        )

        with get_db_session() as db:
            db.add(db_user)
            db.flush()
            # Capture values into local variables while session is open
            assigned_id = db_user.id
            user_dict = {
                "id": assigned_id,
                "name": db_user.name,
                "email": db_user.email,
                "department": db_user.department,
                "graduation_year": db_user.graduation_year,
                "role": db_user.role,
            }

        # Step 7: Mirror record in UserService to ensure consistent in-memory state
        UserService.create_user(
            id=user_dict["id"],
            name=user_dict["name"],
            email=user_dict["email"],
            department=user_dict["department"],
            graduation_year=user_dict["graduation_year"],
            role=user_dict["role"],
        )

        # Step 8: Return safe user dictionary (no credentials exposed)
        return user_dict


# Standalone function alias
register_user = RegistrationService.register_user

__all__ = [
    "RegistrationService",
    "register_user",
]
