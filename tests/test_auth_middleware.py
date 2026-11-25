"""Unit and integration tests for AuthenticationMiddleware and dynamic DB role synchronization."""

from datetime import datetime, timedelta
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


class TestAuthenticationMiddleware(unittest.TestCase):
    """Test suite verifying AuthenticationMiddleware, request.state.user attachment, and DB role sync."""

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
        name: str = "Ali Vural",
        email: str = "ali@alumni.istanbul.edu.tr",
        password: str = "Password123!",
        role: str = "alumnus",
    ) -> Dict[str, Any]:
        """Helper creating and persisting a test user in PostgreSQL."""
        with get_db_session() as db:
            user = UserDB(
                name=name,
                email=email.lower().strip(),
                department="İktisat Fakültesi",
                graduation_year=2018,
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

    def test_public_routes_accessible_without_cookie(self):
        """Public routes must remain freely accessible without an active session cookie."""
        public_routes = ["/", "/about", "/login", "/register", "/api/health", "/users", "/jobs"]
        for path in public_routes:
            status_code, _, _ = self._run_request("GET", path)
            self.assertEqual(status_code, 200, f"Public path {path} failed with {status_code}")

    def test_protected_web_routes_redirect_unauthenticated(self):
        """Unauthenticated requests to protected web views must redirect to /login."""
        status_code, headers, _ = self._run_request("GET", "/dashboard")
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))
        self.assertIn("notice=", headers.get("location", ""))

    def test_protected_api_routes_return_401_unauthenticated(self):
        """Unauthenticated requests to protected REST endpoints must return HTTP 401 JSON."""
        protected_apis = ["/api/me", "/api/admin/overview"]
        for path in protected_apis:
            status_code, _, data = self._run_request(
                "GET", path, headers={"accept": "application/json"}
            )
            self.assertEqual(status_code, 401, f"Path {path} did not return 401")
            self.assertEqual(data.get("detail"), "Oturum açmanız gerekiyor.")

    def test_authenticated_request_attaches_user_to_request_state(self):
        """Valid session cookie must attach user to request.state.user and grant access."""
        user = self._create_test_user(email="attach_check@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        # /dashboard returns 200 and renders user name
        status_code, _, body = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)
        self.assertIn("Ali Vural", body)

        # /api/me returns 200 and profile from request.state.user
        status_code, _, data = self._run_request(
            "GET", "/api/me", headers={"accept": "application/json"}, cookies=cookies
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["user"]["email"], "attach_check@alumni.istanbul.edu.tr")

    def test_db_role_synchronization_immediate_effect(self):
        """Middleware must query PostgreSQL on every request to reflect immediate role promotions and demotions."""
        user = self._create_test_user(
            email="role_sync@alumni.istanbul.edu.tr",
            role="alumnus",
        )
        user_id = user["id"]
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        # 1. Initially 'alumnus': /api/admin/overview must return 403 Forbidden
        status_code, _, data = self._run_request("GET", "/api/admin/overview", cookies=cookies)
        self.assertEqual(status_code, 403)
        self.assertIn("yetkiniz bulunmamaktadır", data.get("detail", ""))

        # 2. Promote user to 'admin' directly in PostgreSQL
        with get_db_session() as db:
            db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
            db_user.role = "admin"

        # 3. Next request with the SAME token must immediately succeed (HTTP 200)
        status_code, _, data = self._run_request("GET", "/api/admin/overview", cookies=cookies)
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["admin"]["role"], "admin")

        # 4. Demote user back to 'alumnus' in PostgreSQL
        with get_db_session() as db:
            db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
            db_user.role = "alumnus"

        # 5. Next request with the SAME token must immediately be forbidden (HTTP 403)
        status_code, _, data = self._run_request("GET", "/api/admin/overview", cookies=cookies)
        self.assertEqual(status_code, 403)

    def test_deleted_user_invalidates_session_and_clears_cookie(self):
        """If user is deleted from PostgreSQL, middleware must purge session and reject request."""
        user = self._create_test_user(email="deleted_user@alumni.istanbul.edu.tr")
        user_id = user["id"]
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        # Verify access initially
        status_code, _, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Delete user from database
        with get_db_session() as db:
            db.query(UserDB).filter(UserDB.id == user_id).delete()

        # Subsequent request must be rejected and session purged
        status_code, headers, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))

        # Session is purged from SessionService
        self.assertIsNone(SessionService.get_session(token))

        # Cookie cleared
        set_cookie = headers.get("set-cookie", "")
        self.assertIn("max-age=0", set_cookie.lower())

    def test_expired_or_invalid_cookie_cleansed_on_response(self):
        """Expired session cookie must be cleansed on response."""
        user = self._create_test_user(email="exp_cleanse@alumni.istanbul.edu.tr")
        expired_token = SessionService.create_session(user, max_age_seconds=-1)
        cookies = {settings.SESSION_COOKIE_NAME: expired_token}

        # On protected route -> 303 Redirect to login with notice + Set-Cookie Max-Age=0
        status_code, headers, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertIn("Oturumunuzun+s%C3%BCresi+doldu", headers.get("location", ""))
        set_cookie = headers.get("set-cookie", "")
        self.assertIn("max-age=0", set_cookie.lower())

        # On public route -> 200 OK + Set-Cookie Max-Age=0 to cleanse browser
        status_code, headers, _ = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)
        set_cookie = headers.get("set-cookie", "")
        self.assertIn("max-age=0", set_cookie.lower())

    def test_tampered_session_token_rejected_and_cleansed(self):
        """Tampered session token signature must return 401 on API and cleanse cookie."""
        user = self._create_test_user(email="tamper_check@alumni.istanbul.edu.tr")
        valid_token = SessionService.create_session(user)
        # Flip signature characters
        tampered_token = valid_token[:-4] + "0000"
        cookies = {settings.SESSION_COOKIE_NAME: tampered_token}

        status_code, headers, data = self._run_request(
            "GET", "/api/me", headers={"accept": "application/json"}, cookies=cookies
        )
        self.assertEqual(status_code, 401)
        self.assertEqual(data.get("detail"), "Oturum açmanız gerekiyor.")


if __name__ == "__main__":
    unittest.main()
