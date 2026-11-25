"""Unit and integration tests for Alumni User Logout, Session Invalidation, and CSRF Protection."""

from datetime import datetime
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password
from app.main import app
from app.models.user_db import UserDB
from app.services.session_service import SessionService, clear_sessions
from app.services.user_service import clear_users


class TestLogout(unittest.TestCase):
    """Test suite verifying Logout functionality, cookie clearing, session invalidation, and CSRF defense."""

    def setUp(self):
        """Clean database and in-memory session/user stores before each test."""
        clear_users()
        clear_sessions()
        with get_db_session() as db:
            db.query(UserDB).delete()

    def tearDown(self):
        """Clean database and in-memory session/user stores after each test."""
        clear_users()
        clear_sessions()
        with get_db_session() as db:
            db.query(UserDB).delete()

    def _create_test_user(
        self,
        name: str = "Mehmet Can",
        email: str = "mehmet@alumni.istanbul.edu.tr",
        password: str = "Password123!",
        role: str = "alumnus",
    ) -> Dict[str, Any]:
        """Helper creating and persisting a test user in PostgreSQL."""
        with get_db_session() as db:
            user = UserDB(
                name=name,
                email=email.lower().strip(),
                department="Hukuk Fakültesi",
                graduation_year=2019,
                hashed_password=hash_password(password),
                role=role,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.flush()
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "graduation_year": user.graduation_year,
                "role": user.role,
            }

    @staticmethod
    def _run_request(
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], Any]:
        """Dispatches an ASGI HTTP request directly to FastAPI app."""
        async def _asgi_call():
            req_headers = dict(headers or {})
            body_bytes = b""

            if cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                req_headers["cookie"] = cookie_str

            if body is not None:
                content_type = req_headers.get("content-type", "")
                if "application/x-www-form-urlencoded" in content_type:
                    if isinstance(body, dict):
                        body_bytes = urllib.parse.urlencode(body).encode("utf-8")
                    elif isinstance(body, str):
                        body_bytes = body.encode("utf-8")
                    else:
                        body_bytes = bytes(body)
                else:
                    if "content-type" not in req_headers:
                        req_headers["content-type"] = "application/json"
                    if isinstance(body, (dict, list)):
                        body_bytes = json.dumps(body).encode("utf-8")
                    elif isinstance(body, str):
                        body_bytes = body.encode("utf-8")
                    else:
                        body_bytes = bytes(body)

            req_headers["content-length"] = str(len(body_bytes))

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": method.upper(),
                "path": path,
                "raw_path": path.encode("latin-1"),
                "query_string": b"",
                "headers": [
                    (k.lower().encode("latin-1"), v.encode("latin-1"))
                    for k, v in req_headers.items()
                ],
            }

            request_sent = False

            async def receive():
                nonlocal request_sent
                if not request_sent:
                    request_sent = True
                    return {
                        "type": "http.request",
                        "body": body_bytes,
                        "more_body": False,
                    }
                return {"type": "http.request", "body": b"", "more_body": False}

            response_headers: Dict[str, str] = {}
            response_chunks = []
            status_code = [200]

            async def send(message):
                if message["type"] == "http.response.start":
                    status_code[0] = message["status"]
                    for k, v in message.get("headers", []):
                        key = k.decode("latin-1").lower()
                        val = v.decode("latin-1")
                        if key in response_headers and key == "set-cookie":
                            response_headers[key] = f"{response_headers[key]}, {val}"
                        else:
                            response_headers[key] = val
                elif message["type"] == "http.response.body":
                    response_chunks.append(message.get("body", b""))

            await app(scope, receive, send)

            raw_body = b"".join(response_chunks).decode("utf-8")
            res_content_type = response_headers.get("content-type", "")
            if "application/json" in res_content_type:
                try:
                    parsed_json = json.loads(raw_body)
                    return status_code[0], response_headers, parsed_json
                except Exception:
                    pass
            return status_code[0], response_headers, raw_body

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_asgi_call())
        finally:
            loop.close()

    def test_successful_logout_html_form(self):
        """POST /logout with valid session and CSRF token invalidates session, clears cookie, and redirects."""
        user = self._create_test_user(email="logout_user@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        session = SessionService.get_session(token)
        csrf_token = session["csrf_token"]

        payload = {"csrf_token": csrf_token}
        headers = {"content-type": "application/x-www-form-urlencoded"}
        cookies = {settings.SESSION_COOKIE_NAME: token}

        status_code, res_headers, _ = self._run_request("POST", "/logout", body=payload, headers=headers, cookies=cookies)

        # 1. Redirect to login with notice
        self.assertEqual(status_code, 303)
        self.assertIn("/login", res_headers.get("location", ""))

        # 2. Server-side session is completely invalidated
        self.assertIsNone(SessionService.get_session(token))

        # 3. Session cookie is cleared securely
        set_cookie = res_headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie)
        self.assertIn("max-age=0", set_cookie.lower())
        self.assertIn("httponly", set_cookie.lower())
        self.assertIn("samesite=lax", set_cookie.lower())

    def test_successful_logout_json_api(self):
        """POST /api/logout with valid X-CSRF-Token returns 200, invalidates session, and clears cookie."""
        user = self._create_test_user(email="api_logout@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        session = SessionService.get_session(token)
        csrf_token = session["csrf_token"]

        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "x-csrf-token": csrf_token,
        }
        cookies = {settings.SESSION_COOKIE_NAME: token}

        status_code, res_headers, data = self._run_request("POST", "/api/logout", headers=headers, cookies=cookies)

        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("kapatıldı", data.get("message", ""))

        # Invalidate session
        self.assertIsNone(SessionService.get_session(token))

        # Cookie cleared
        set_cookie = res_headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie)
        self.assertIn("max-age=0", set_cookie.lower())

    def test_protected_routes_inaccessible_after_logout(self):
        """Logged-out user cannot access protected web or API routes with old session cookie."""
        user = self._create_test_user(email="protect_after@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        session = SessionService.get_session(token)
        csrf_token = session["csrf_token"]

        cookies = {settings.SESSION_COOKIE_NAME: token}

        # Verify access while logged in
        status_code, _, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Log out
        self._run_request(
            "POST",
            "/logout",
            body={"csrf_token": csrf_token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            cookies=cookies,
        )

        # Attempt to access /dashboard with old cookie -> 303 Redirect to /login
        status_code, headers, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))

        # Attempt to access /api/me with old cookie -> 401 Unauthorized
        status_code, _, data = self._run_request("GET", "/api/me", cookies=cookies)
        self.assertEqual(status_code, 401)
        self.assertIn("detail", data)

        # Attempt to access /api/admin/overview with old cookie -> 401 Unauthorized
        status_code, _, data = self._run_request("GET", "/api/admin/overview", cookies=cookies)
        self.assertEqual(status_code, 401)

    def test_logout_csrf_protection_missing_token_rejected(self):
        """POST /logout without CSRF token must be rejected (403) and keep session active."""
        user = self._create_test_user(email="csrf_missing@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)

        cookies = {settings.SESSION_COOKIE_NAME: token}
        headers = {"content-type": "application/x-www-form-urlencoded"}

        # Submitting without csrf_token
        status_code, _, body = self._run_request("POST", "/logout", body={}, headers=headers, cookies=cookies)
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF", body)

        # Session MUST remain active
        self.assertIsNotNone(SessionService.get_session(token))

    def test_logout_csrf_protection_invalid_token_rejected(self):
        """POST /logout with invalid CSRF token must be rejected (403) and keep session active."""
        user = self._create_test_user(email="csrf_invalid@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)

        cookies = {settings.SESSION_COOKIE_NAME: token}
        headers = {"content-type": "application/x-www-form-urlencoded"}

        # Submitting with forged token
        status_code, _, body = self._run_request(
            "POST",
            "/logout",
            body={"csrf_token": "forged_cross_site_token"},
            headers=headers,
            cookies=cookies,
        )
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF", body)

        # Session MUST remain active
        self.assertIsNotNone(SessionService.get_session(token))

    def test_logout_csrf_protection_untrusted_origin_rejected(self):
        """POST /logout with untrusted Origin must be rejected (403) and keep session active."""
        user = self._create_test_user(email="origin_logout@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        session = SessionService.get_session(token)
        csrf_token = session["csrf_token"]

        cookies = {settings.SESSION_COOKIE_NAME: token}
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "http://evil.com",
        }

        status_code, _, data = self._run_request(
            "POST",
            "/logout",
            body={"csrf_token": csrf_token},
            headers=headers,
            cookies=cookies,
        )
        self.assertEqual(status_code, 403)

        # Session MUST remain active
        self.assertIsNotNone(SessionService.get_session(token))

    def test_get_logout_does_not_mutate_session(self):
        """GET /logout must not invalidate session (prevents GET logout attacks); redirects safely."""
        user = self._create_test_user(email="get_logout@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)

        cookies = {settings.SESSION_COOKIE_NAME: token}

        # Authenticated GET /logout redirects to dashboard
        status_code, headers, _ = self._run_request("GET", "/logout", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertEqual(headers.get("location"), "/dashboard")

        # Session MUST remain intact
        self.assertIsNotNone(SessionService.get_session(token))

        # Unauthenticated GET /logout redirects to login
        status_code, headers, _ = self._run_request("GET", "/logout")
        self.assertEqual(status_code, 303)
        self.assertEqual(headers.get("location"), "/login")

    def test_logout_button_present_in_dashboard_and_navbar(self):
        """Authenticated dashboard view must render Logout form and button."""
        user = self._create_test_user(email="ui_check@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        status_code, _, body = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Must have logout form action and button
        self.assertIn('action="/logout"', body)
        self.assertIn('method="POST"', body)
        self.assertIn("Çıkış Yap", body)
        self.assertIn("dashboardLogoutBtn", body)

    def test_unauthenticated_logout_handled_gracefully(self):
        """POST /logout without active session redirects to login without error."""
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status_code, res_headers, _ = self._run_request("POST", "/logout", body={}, headers=headers)
        self.assertEqual(status_code, 303)
        self.assertIn("/login", res_headers.get("location", ""))


if __name__ == "__main__":
    unittest.main()
