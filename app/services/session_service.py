"""Cryptographically secure session management for authenticated users.

Provides signed session tokens using HMAC-SHA256 with 256-bit random entropy,
in-memory session storage, expiration checks, and session invalidation.
"""

from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional, Union

from app.core.config import settings
from app.core.csrf import generate_session_csrf_token
from app.models.user_db import UserDB


class SessionService:
    """In-memory session manager with signed tokens and expiry tracking."""

    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _sign_token(cls, raw_id: str) -> str:
        """Computes HMAC-SHA256 signature for a raw session identifier."""
        signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            raw_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{raw_id}.{signature}"

    @classmethod
    def _verify_and_extract_raw_id(cls, signed_token: str) -> Optional[str]:
        """Validates token signature using constant-time comparison and returns raw ID."""
        if not signed_token or not isinstance(signed_token, str) or "." not in signed_token:
            return None

        parts = signed_token.split(".", 1)
        if len(parts) != 2:
            return None

        raw_id, signature = parts
        if not raw_id or not signature:
            return None

        expected = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            raw_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing side-channel attacks
        if not hmac.compare_digest(signature, expected):
            return None

        return raw_id

    @classmethod
    def create_session(
        cls,
        user: Union[UserDB, Dict[str, Any]],
        max_age_seconds: Optional[int] = None,
    ) -> str:
        """Creates a new session for an authenticated user and returns a signed token.

        Args:
            user: UserDB ORM instance or user data dictionary.
            max_age_seconds: Lifetime of the session in seconds (default from settings).

        Returns:
            Signed session token string.
        """
        max_age = max_age_seconds or settings.SESSION_MAX_AGE
        raw_id = secrets.token_urlsafe(32)
        signed_token = cls._sign_token(raw_id)

        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=max_age)

        if isinstance(user, UserDB):
            user_id = user.id
            email = user.email
            name = user.name
            role = user.role
            department = user.department
            graduation_year = user.graduation_year
        else:
            user_id = user["id"]
            email = user["email"]
            name = user["name"]
            role = user.get("role", "alumnus")
            department = user.get("department", "")
            graduation_year = user.get("graduation_year", 0)

        csrf_token = generate_session_csrf_token(raw_id)

        cls._sessions[raw_id] = {
            "session_id": raw_id,
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": role,
            "department": department,
            "graduation_year": graduation_year,
            "csrf_token": csrf_token,
            "created_at": now,
            "expires_at": expires_at,
        }

        return signed_token

    @classmethod
    def get_csrf_token(cls, signed_token: str) -> Optional[str]:
        """Returns the synchronizer CSRF token associated with a signed session token."""
        session = cls.get_session(signed_token)
        return session.get("csrf_token") if session else None

    @classmethod
    def get_session(cls, signed_token: str) -> Optional[Dict[str, Any]]:
        """Retrieves active session data if token is valid and not expired.

        Args:
            signed_token: Signed session token from client cookie.

        Returns:
            Session data dictionary if valid, None otherwise.
        """
        raw_id = cls._verify_and_extract_raw_id(signed_token)
        if not raw_id:
            return None

        session_data = cls._sessions.get(raw_id)
        if not session_data:
            return None

        # Check expiration
        if datetime.utcnow() > session_data["expires_at"]:
            cls._sessions.pop(raw_id, None)
            return None

        return dict(session_data)

    @classmethod
    def delete_session(cls, signed_token: str) -> bool:
        """Deletes a session from the active store.

        Args:
            signed_token: Signed session token string.

        Returns:
            True if session was found and removed, False otherwise.
        """
        raw_id = cls._verify_and_extract_raw_id(signed_token)
        if not raw_id:
            return False

        if raw_id in cls._sessions:
            del cls._sessions[raw_id]
            return True
        return False

    @classmethod
    def clear_sessions(cls) -> None:
        """Clears all active sessions (used primarily for test isolation)."""
        cls._sessions.clear()


# Standalone function aliases
create_session = SessionService.create_session
get_session = SessionService.get_session
delete_session = SessionService.delete_session
clear_sessions = SessionService.clear_sessions

__all__ = [
    "SessionService",
    "create_session",
    "get_session",
    "delete_session",
    "clear_sessions",
]
