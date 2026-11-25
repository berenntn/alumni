"""FastAPI dependency providers for authentication and authorization."""

from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.services.session_service import SessionService


def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extracts session cookie and retrieves user session data if present and valid.

    Args:
        request: Incoming FastAPI Request.

    Returns:
        User session dict if authenticated, None otherwise.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None
    return SessionService.get_session(token)


def get_current_user(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Dependency requiring an authenticated user session.

    Args:
        request: Incoming FastAPI Request.
        user: Resolved user from get_current_user_optional.

    Returns:
        Authenticated user session dict.

    Raises:
        HTTPException(401): If no valid session is present.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor.",
        )
    return user


def require_role(required_role: str) -> Callable:
    """Dependency factory enforcing that the authenticated user possesses a specific role.

    Args:
        required_role: Required role name (e.g. 'admin', 'alumnus').

    Returns:
        FastAPI dependency callable returning user or raising 403 Forbidden.
    """
    def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "alumnus")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır.",
            )
        return current_user

    return role_checker


__all__ = [
    "get_current_user_optional",
    "get_current_user",
    "require_role",
]
