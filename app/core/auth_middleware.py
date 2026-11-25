"""Centralized Authentication Middleware for the Alumni Tracking System.

Enforces:
1. Session extraction from HTTP cookie or Authorization: Bearer <token> header.
2. Cryptographic signature and expiration validation via SessionService.
3. Dynamic synchronization of current user roles and attributes from PostgreSQL UserDB,
   preventing stale roles or client-controlled role tampering.
4. Attachment of the authenticated user dictionary to request.state.user.
5. Consistent route protection:
   - Safe read operations on public resources remain accessible without credentials.
   - Private GET endpoints and state-changing write operations (POST, PUT, PATCH, DELETE)
     strictly require an authenticated session unless explicitly exempted (login, register, logout).
   - Web requests to protected routes: HTTP 303 Redirect to /login with informative notice.
   - API requests to protected routes: HTTP 401 JSON error responses.
6. Invalidation and cookie cleansing for expired, deleted, or tampered sessions.
"""

import logging
import re
from typing import Optional, Pattern, Sequence, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette import status
from sqlalchemy import func, or_

from app.core.config import settings
from app.core.database import get_db_session
from app.models.user_db import UserDB
from app.services.session_service import SessionService

logger = logging.getLogger("app.middleware.auth")

# Specific GET route patterns that require an authenticated session
PROTECTED_GET_PATTERNS: Sequence[Pattern] = (
    re.compile(r"^/dashboard(/.*)?$"),
    re.compile(r"^/admin(/.*)?$"),
    re.compile(r"^/api/me(/.*)?$"),
    re.compile(r"^/api/admin(/.*)?$"),
    re.compile(r"^/applications(/.*)?$"),
    re.compile(r"^/api/applications(/.*)?$"),
    re.compile(r"^/api/users/\d+/applications(/.*)?$"),
    re.compile(r"^/api/job-postings/\d+/applications(/.*)?$"),
    re.compile(r"^/jobs/\d+/apply(/.*)?$"),
    re.compile(r"^/users/\d+/edit(/.*)?$"),
    re.compile(r"^/announcements/\d+/edit(/.*)?$"),
)

# State-changing paths that have a justified public use case
PUBLIC_STATE_CHANGING_PATHS: Set[str] = {
    "/login",
    "/api/login",
    "/register",
    "/api/register",
    "/logout",
    "/api/logout",
}


def is_route_protected(path: str, method: str = "GET") -> bool:
    """Determines whether a given request path and method requires an authenticated session."""
    method_upper = method.upper()
    norm_path = path.rstrip("/") if path != "/" else "/"

    # Safe read methods: only specific private GET endpoints require authentication
    if method_upper in ("GET", "HEAD", "OPTIONS"):
        for pattern in PROTECTED_GET_PATTERNS:
            if pattern.match(norm_path):
                return True
        return False

    # State-changing methods (POST, PUT, PATCH, DELETE):
    # Require authentication unless explicitly exempted (login, register, logout)
    if norm_path in PUBLIC_STATE_CHANGING_PATHS:
        return False

    return True


def is_json_preferred(request: Request) -> bool:
    """Detects whether client expects a JSON response."""
    accept = request.headers.get("accept", "").lower()
    content_type = request.headers.get("content-type", "").lower()
    return (
        "application/json" in accept
        or "application/json" in content_type
        or request.url.path.startswith("/api/")
    )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Centralized authentication middleware running on every incoming HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Initialize request state
        request.state.user = None
        session_invalid_or_expired = False

        # 2. Inspect session credential (cookie or Bearer token)
        session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        has_cookie = bool(session_token)

        auth_header = request.headers.get("authorization", "").strip()
        has_bearer = bool(auth_header.lower() == "bearer" or auth_header.lower().startswith("bearer "))

        if not session_token and has_bearer:
            if auth_header.lower().startswith("bearer "):
                session_token = auth_header[7:].strip()
            else:
                session_token = ""
            if not session_token:
                session_invalid_or_expired = True

        if session_token:
            session_data = SessionService.get_session(session_token)
            if session_data:
                # Valid session token found; synchronize role and attributes from PostgreSQL
                user_id = session_data.get("user_id")
                email = session_data.get("email", "")

                try:
                    with get_db_session() as db:
                        user_record = (
                            db.query(
                                UserDB.id,
                                UserDB.name,
                                UserDB.email,
                                UserDB.role,
                                UserDB.department,
                                UserDB.graduation_year,
                            )
                            .filter(
                                or_(
                                    UserDB.id == user_id,
                                    func.lower(UserDB.email) == email.lower(),
                                )
                            )
                            .first()
                        )

                    if user_record:
                        # Synchronize user dictionary with latest DB state
                        request.state.user = {
                            **session_data,
                            "user_id": user_record.id,
                            "role": user_record.role or "alumnus",
                            "name": user_record.name,
                            "email": user_record.email,
                            "department": user_record.department,
                            "graduation_year": user_record.graduation_year,
                        }
                    else:
                        # User was deleted from database; invalidate session
                        logger.warning(
                            f"User ID {user_id} not found in database. Invalidating session."
                        )
                        SessionService.delete_session(session_token)
                        session_invalid_or_expired = True

                except Exception as e:
                    logger.error(f"Error querying user from database in auth middleware: {e}")
                    # In case of DB query error, retain in-memory session to prevent transient lockouts
                    request.state.user = dict(session_data)
            else:
                # Token was present but session is invalid, expired, or tampered
                session_invalid_or_expired = True

        # 3. Route Protection & Bearer Token Enforcement
        path = request.url.path
        method = request.method
        route_protected = is_route_protected(path, method)

        # Enforce rejection:
        # A) Protected route requested by unauthenticated caller
        # B) Caller explicitly provided an invalid, expired, or revoked Bearer token (on any route)
        if (route_protected and request.state.user is None) or (has_bearer and request.state.user is None):
            logger.info(f"Unauthenticated request to '{method} {path}' rejected.")
            if has_bearer or is_json_preferred(request):
                return JSONResponse(
                    content={"detail": "Oturum açmanız gerekiyor."},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"} if has_bearer else {},
                )

            notice = (
                "Oturumunuzun+süresi+doldu.+Lütfen+tekrar+giriş+yapın."
                if session_invalid_or_expired
                else "Bu+sayfaya+erişmek+için+lütfen+giriş+yapın."
            )
            response = RedirectResponse(
                url=f"/login?notice={notice}",
                status_code=status.HTTP_303_SEE_OTHER,
            )
            if session_invalid_or_expired and has_cookie:
                response.delete_cookie(
                    key=settings.SESSION_COOKIE_NAME,
                    path="/",
                    httponly=True,
                    samesite="lax",
                    secure=settings.session_cookie_secure,
                )
            return response

        # Enforce Admin Role Authorization for /admin* routes
        is_admin_route = path.startswith("/admin") or path.startswith("/api/admin")
        if request.state.user is not None and is_admin_route and request.state.user.get("role") != "admin":
            logger.warning(
                f"Forbidden access to '{path}' by user '{request.state.user.get('email')}' with role '{request.state.user.get('role')}'."
            )
            if is_json_preferred(request):
                return JSONResponse(
                    content={"detail": "Bu işlem için yetkiniz bulunmamaktadır."},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            try:
                from app.core.exceptions import templates
                return templates.TemplateResponse(
                    request=request,
                    name="403.html",
                    context={
                        "app_name": settings.APP_NAME,
                        "app_title_tr": settings.APP_TITLE_TR,
                        "app_description": settings.APP_DESCRIPTION,
                        "detail": "Bu sayfaya erişim yetkiniz bulunmamaktadır.",
                        "user": request.state.user,
                    },
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            except Exception:
                return JSONResponse(
                    content={"detail": "Bu işlem için yetkiniz bulunmamaktadır."},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        # 4. Proceed through middleware pipeline
        response = await call_next(request)

        # 5. Cleanse client browser if cookie was present but invalid/expired on a public route
        if session_invalid_or_expired and has_cookie and not route_protected:
            response.delete_cookie(
                key=settings.SESSION_COOKIE_NAME,
                path="/",
                httponly=True,
                samesite="lax",
                secure=settings.session_cookie_secure,
            )

        return response
