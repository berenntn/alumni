"""FastAPI / Starlette Middleware enforcing explicit CSRF and Origin protection.

Enforces:
1. Origin / Referer header validation on all state-changing requests (POST, PUT, PATCH, DELETE).
2. Login form CSRF token validation on POST /login.
3. Synchronizer CSRF token validation on any state-changing request carrying an active session cookie.
"""

import json
import logging
import re
from typing import Optional
import urllib.parse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, HTMLResponse
from starlette import status

from app.core.config import settings
from app.core.csrf import (
    is_origin_allowed,
    validate_login_csrf_token,
    validate_session_csrf_token,
)
from app.services.session_service import SessionService

logger = logging.getLogger("app.middleware.csrf")

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def extract_csrf_token(request: Request, body_bytes: bytes) -> Optional[str]:
    """Extracts CSRF token from request headers, form body, or JSON body."""
    # 1. Custom HTTP headers (standard for AJAX / SPA / APIs)
    header_val = (
        request.headers.get("x-csrf-token")
        or request.headers.get("x-csrftoken")
        or request.headers.get("csrf-token")
    )
    if header_val:
        return header_val.strip()

    if not body_bytes:
        return None

    content_type = request.headers.get("content-type", "").lower()

    # 2. Form urlencoded body
    if "application/x-www-form-urlencoded" in content_type:
        try:
            parsed = urllib.parse.parse_qs(body_bytes.decode("utf-8", errors="ignore"))
            vals = parsed.get("csrf_token") or parsed.get("csrf-token")
            if vals and vals[0]:
                return vals[0].strip()
        except Exception:
            pass

    # 3. JSON body
    elif "application/json" in content_type:
        try:
            data = json.loads(body_bytes.decode("utf-8", errors="ignore"))
            if isinstance(data, dict):
                val = data.get("csrf_token") or data.get("csrf-token")
                if val and isinstance(val, str):
                    return val.strip()
        except Exception:
            pass

    # 4. Multipart form-data
    elif "multipart/form-data" in content_type:
        try:
            match = re.search(
                r'name=["\']csrf_token["\']\r\n\r\n([^\r\n]+)',
                body_bytes.decode("latin-1", errors="ignore"),
            )
            if match:
                return match.group(1).strip()
        except Exception:
            pass

    return None


def _is_json_preferred(request: Request) -> bool:
    """Detects whether client expects a JSON response."""
    accept = request.headers.get("accept", "").lower()
    content_type = request.headers.get("content-type", "").lower()
    return (
        "application/json" in accept
        or "application/json" in content_type
        or request.url.path.startswith("/api/")
    )


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing defense-in-depth CSRF and Origin checks."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safe HTTP methods do not mutate state; pass through immediately
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # 1. Validate Origin / Referer against untrusted external domains
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        host = request.headers.get("host")

        if origin and not is_origin_allowed(origin, host):
            logger.warning(
                f"CSRF Origin check failed: untrusted Origin '{origin}' on {request.method} {request.url.path}"
            )
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Cross-origin request rejected: Untrusted Origin.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not origin and referer and not is_origin_allowed(referer, host):
            logger.warning(
                f"CSRF Referer check failed: untrusted Referer '{referer}' on {request.method} {request.url.path}"
            )
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Cross-origin request rejected: Untrusted Referer.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Cache body bytes so downstream handlers and CSRF extraction can inspect it
        body_bytes = await request.body()
        submitted_csrf = extract_csrf_token(request, body_bytes)

        # 2. Login Form CSRF Validation (POST /login)
        if request.url.path == "/login" and request.method == "POST":
            # For the web login form, require valid login CSRF token
            if not submitted_csrf or not validate_login_csrf_token(submitted_csrf):
                logger.warning(f"Login CSRF validation failed on POST /login (token present: {bool(submitted_csrf)})")
                if _is_json_preferred(request):
                    return JSONResponse(
                        content={
                            "status": "error",
                            "message": "CSRF doğrulaması başarısız. Lütfen sayfayı yenileyip tekrar deneyin.",
                        },
                        status_code=status.HTTP_403_FORBIDDEN,
                    )
                return HTMLResponse(
                    content=(
                        "<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
                        "<title>403 Yetkisiz Erişim | CSRF Doğrulaması Başarısız</title>"
                        "<style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f7;color:#1d1d1f;}"
                        ".box{background:#fff;padding:2.5rem;border-radius:18px;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:440px;text-align:center;}"
                        "h1{font-size:1.5rem;margin-bottom:0.75rem;color:#ff3b30;}p{font-size:0.95rem;color:#6e6e73;line-height:1.5;margin-bottom:1.5rem;}"
                        "a{display:inline-block;padding:0.6rem 1.4rem;background:#0071e3;color:#fff;text-decoration:none;border-radius:980px;font-weight:600;font-size:0.9rem;}</style></head>"
                        "<body><div class='box'><h1>CSRF Doğrulaması Başarısız</h1>"
                        "<p>Güvenlik belirteci geçersiz veya oturum süresi dolmuş olabilir. Lütfen giriş sayfasına dönüp tekrar deneyin.</p>"
                        "<a href='/login'>Giriş Sayfasına Dön</a></div></body></html>"
                    ),
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        # 3. Synchronizer CSRF Token Validation for Cookie-Authenticated Requests
        session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if session_cookie:
            active_session = getattr(request.state, "user", None)
            if not active_session:
                active_session = SessionService.get_session(session_cookie)

            if active_session:
                expected_csrf = active_session.get("csrf_token")
                if not submitted_csrf or not validate_session_csrf_token(submitted_csrf, expected_csrf):
                    logger.warning(
                        f"Synchronizer CSRF check failed for user {active_session.get('user_id')} on "
                        f"{request.method} {request.url.path} (token provided: {bool(submitted_csrf)})"
                    )
                    if _is_json_preferred(request):
                        return JSONResponse(
                            content={
                                "status": "error",
                                "message": "CSRF doğrulaması başarısız. Oturum açmış kullanıcılar için geçerli bir CSRF belirteci (X-CSRF-Token) gereklidir.",
                            },
                            status_code=status.HTTP_403_FORBIDDEN,
                        )
                    return HTMLResponse(
                        content=(
                            "<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
                            "<title>403 Yetkisiz Erişim | CSRF Doğrulaması Başarısız</title>"
                            "<style>body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f7;color:#1d1d1f;}"
                            ".box{background:#fff;padding:2.5rem;border-radius:18px;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:440px;text-align:center;}"
                            "h1{font-size:1.5rem;margin-bottom:0.75rem;color:#ff3b30;}p{font-size:0.95rem;color:#6e6e73;line-height:1.5;margin-bottom:1.5rem;}"
                            "a{display:inline-block;padding:0.6rem 1.4rem;background:#0071e3;color:#fff;text-decoration:none;border-radius:980px;font-weight:600;font-size:0.9rem;}</style></head>"
                            "<body><div class='box'><h1>CSRF Doğrulaması Başarısız</h1>"
                            "<p>İşleminiz için güvenlik doğrulaması yapılamadı. Lütfen sayfayı yenileyip işlemi tekrarlayınız.</p>"
                            "<a href='/dashboard'>Panele Dön</a></div></body></html>"
                        ),
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

        return await call_next(request)
