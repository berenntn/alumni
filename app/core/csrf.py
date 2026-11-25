"""CSRF protection services, token generators, and origin validation.

Implements:
1. Cryptographically signed, expiring login CSRF tokens for unauthenticated login forms.
2. Synchronizer CSRF tokens bound to authenticated user sessions.
3. Origin / Referer header validation against server host for cross-origin defense.
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Set
import urllib.parse
from starlette.requests import Request

from app.core.config import settings


LOGIN_CSRF_MAX_AGE: int = 3600  # 1 hour validity for login form tokens


def generate_login_csrf_token() -> str:
    """Generates an HMAC-signed, timestamped CSRF token for the login form."""
    nonce = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    payload = f"login_csrf:{nonce}:{timestamp}".encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return f"{nonce}.{timestamp}.{signature}"


def validate_login_csrf_token(token: Optional[str], max_age_seconds: int = LOGIN_CSRF_MAX_AGE) -> bool:
    """Validates an incoming login CSRF token in constant time.

    Args:
        token: Submitted token string in '<nonce>.<timestamp>.<signature>' format.
        max_age_seconds: Maximum allowed age in seconds.

    Returns:
        True if valid and unexpired, False otherwise.
    """
    if not token or not isinstance(token, str) or "." not in token:
        return False

    parts = token.strip().split(".")
    if len(parts) != 3:
        return False

    nonce, ts_str, signature = parts
    try:
        timestamp = int(ts_str)
    except (ValueError, TypeError):
        return False

    now = int(time.time())
    # Reject expired tokens or tokens with future timestamps (> 5 minutes clock skew)
    if (now - timestamp > max_age_seconds) or (timestamp > now + 300):
        return False

    payload = f"login_csrf:{nonce}:{timestamp}".encode("utf-8")
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def generate_session_csrf_token(raw_session_id: str) -> str:
    """Generates a synchronizer CSRF token bound to a specific user session ID."""
    payload = f"session_csrf:{raw_session_id}".encode("utf-8")
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def validate_session_csrf_token(submitted_token: Optional[str], expected_token: Optional[str]) -> bool:
    """Compares submitted CSRF token against the session token using constant-time comparison."""
    if not submitted_token or not expected_token:
        return False
    if not isinstance(submitted_token, str) or not isinstance(expected_token, str):
        return False
    return hmac.compare_digest(submitted_token.strip(), expected_token.strip())


def is_origin_allowed(
    origin: Optional[str],
    host: Optional[str],
    allowed_hosts: Optional[Set[str]] = None,
) -> bool:
    """Validates that an incoming Origin or Referer matches the server's Host or allowed set.

    Args:
        origin: Full origin URL (e.g. 'http://localhost:8000' or 'https://alumni.istanbul.edu.tr').
        host: Request Host header (e.g. 'localhost:8000' or 'testserver').
        allowed_hosts: Optional set of allowed domain/host strings.

    Returns:
        True if allowed, False if cross-origin attack detected.
    """
    if not origin:
        return True

    try:
        parsed = urllib.parse.urlparse(origin)
    except Exception:
        return False

    origin_host = parsed.netloc.lower()
    if not origin_host:
        return False

    target_host = (host or "").lower().strip()
    if origin_host == target_host:
        return True

    # Check against standard test/local hosts
    default_allowed = {
        "testserver",
        "localhost",
        "localhost:8000",
        "127.0.0.1",
        "127.0.0.1:8000",
        f"{settings.HOST}:{settings.PORT}".lower(),
    }
    if allowed_hosts:
        default_allowed.update(h.lower() for h in allowed_hosts)

    return origin_host in default_allowed
