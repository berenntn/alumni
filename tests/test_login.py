"""Unit and integration tests for Alumni User Login, Session Management, and Protected Routes."""

from datetime import datetime, timedelta
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.csrf import generate_login_csrf_token
from app.core.database import get_db_session
from app.core.security import hash_password
from app.main import app
from app.models.user_db import UserDB
from app.services.session_service import SessionService, clear_sessions
from app.services.user_service import clear_users


class TestLogin(unittest.TestCase):
    """Test suite verifying Login authentication, session cookies, route protection, and RBAC."""

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
        name: str = "Ahmet Yılmaz",
        email: str = "ahmet@alumni.istanbul.edu.tr",
        password: str = "Password123!",
        role: str = "alumnus",
    ) -> Dict[str, Any]:
        """Helper creating and persisting a test user in PostgreSQL."""
        with get_db_session() as db:
            user = UserDB(
                name=name,
                email=email.lower().strip(),
                department="Bilgisayar Mühendisliği",
                graduation_year=2021,
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
                        # Decode headers, preserve multi-value set-cookie if any
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

    def test_get_login_page(self):
        """GET /login should return HTTP 200 with email and password fields."""
        status_code, headers, body = self._run_request("GET", "/login")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn('name="email"', body)
        self.assertIn('name="password"', body)
        self.assertIn("Tekrar Hoş Geldiniz", body)

    def test_get_login_page_redirects_when_authenticated(self):
        """GET /login should redirect to /dashboard if an active session cookie is present."""
        self._create_test_user(email="logged@alumni.istanbul.edu.tr")
        token = SessionService.create_session({
            "id": 1,
            "email": "logged@alumni.istanbul.edu.tr",
            "name": "Logged User",
            "role": "alumnus",
            "department": "CS",
            "graduation_year": 2020,
        })
        cookies = {settings.SESSION_COOKIE_NAME: token}
        status_code, headers, _ = self._run_request("GET", "/login", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertEqual(headers.get("location"), "/dashboard")

    def test_successful_login_html_form(self):
        """POST /login with valid form and CSRF token returns HTTP 303 to /dashboard and sets HttpOnly cookie."""
        self._create_test_user(email="test@alumni.istanbul.edu.tr", password="CorrectPassword123")
        csrf_token = generate_login_csrf_token()
        payload = {
            "email": "test@alumni.istanbul.edu.tr",
            "password": "CorrectPassword123",
            "csrf_token": csrf_token,
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status_code, res_headers, _ = self._run_request("POST", "/login", body=payload, headers=headers)

        self.assertEqual(status_code, 303)
        self.assertEqual(res_headers.get("location"), "/dashboard")

        # Verify session cookie
        set_cookie = res_headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("samesite=lax", set_cookie.lower())

        # Verify session created in service
        cookie_val = set_cookie.split(";")[0].split("=")[1]
        session = SessionService.get_session(cookie_val)
        self.assertIsNotNone(session)
        self.assertEqual(session["email"], "test@alumni.istanbul.edu.tr")

    def test_login_page_renders_csrf_token_field(self):
        """GET /login must render an HTML form with a valid hidden csrf_token field."""
        status_code, _, body = self._run_request("GET", "/login")
        self.assertEqual(status_code, 200)
        self.assertIn('name="csrf_token"', body)
        self.assertIn('type="hidden"', body)

    def test_login_html_form_csrf_rejection(self):
        """POST /login without CSRF token or with invalid token must be rejected with HTTP 403."""
        self._create_test_user(email="csrf_target@alumni.istanbul.edu.tr", password="Password123!")

        # 1. Missing CSRF token
        payload_no_csrf = {
            "email": "csrf_target@alumni.istanbul.edu.tr",
            "password": "Password123!",
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status_code, _, body = self._run_request("POST", "/login", body=payload_no_csrf, headers=headers)
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF Doğrulaması Başarısız", body)

        # 2. Invalid / forged CSRF token
        payload_invalid_csrf = {
            "email": "csrf_target@alumni.istanbul.edu.tr",
            "password": "Password123!",
            "csrf_token": "forged_or_tampered_csrf_token",
        }
        status_code, _, body = self._run_request("POST", "/login", body=payload_invalid_csrf, headers=headers)
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF Doğrulaması Başarısız", body)

    def test_successful_login_json_api(self):
        """POST /api/login with valid JSON returns HTTP 200, safe user data, and session cookie."""
        self._create_test_user(email="api_user@alumni.istanbul.edu.tr", password="ApiPassword123")
        payload = {
            "email": "api_user@alumni.istanbul.edu.tr",
            "password": "ApiPassword123",
        }
        status_code, res_headers, data = self._run_request(
            "POST",
            "/api/login",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("redirect_url"), "/dashboard")
        user = data.get("data", {})
        self.assertEqual(user.get("email"), "api_user@alumni.istanbul.edu.tr")
        self.assertEqual(user.get("role"), "alumnus")
        self.assertNotIn("password", user)
        self.assertNotIn("hashed_password", user)

        set_cookie = res_headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie)
        self.assertIn("HttpOnly", set_cookie)

    def test_login_incorrect_password(self):
        """Submitting wrong password must return error and set no session cookie."""
        self._create_test_user(email="real@alumni.istanbul.edu.tr", password="RealPassword123")
        payload = {
            "email": "real@alumni.istanbul.edu.tr",
            "password": "WrongPassword456",
        }
        status_code, res_headers, data = self._run_request(
            "POST",
            "/api/login",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("hatalı", data.get("message", "").lower())
        self.assertNotIn("set-cookie", res_headers)

    def test_login_unknown_email(self):
        """Submitting non-existent email must return generic error and set no cookie."""
        payload = {
            "email": "nonexistent@alumni.istanbul.edu.tr",
            "password": "AnyPassword123",
        }
        status_code, res_headers, data = self._run_request(
            "POST",
            "/api/login",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("hatalı", data.get("message", "").lower())
        self.assertNotIn("set-cookie", res_headers)

    def test_login_missing_or_empty_credentials(self):
        """Submitting empty email or password returns HTTP 400."""
        payloads = [
            {"email": "", "password": "Password123"},
            {"email": "valid@alumni.istanbul.edu.tr", "password": ""},
            {"email": "invalid-email-format", "password": "Password123"},
        ]
        for p in payloads:
            status_code, _, data = self._run_request(
                "POST",
                "/api/login",
                body=p,
                headers={"content-type": "application/json", "accept": "application/json"},
            )
            self.assertEqual(status_code, 400)
            self.assertEqual(data.get("status"), "error")

    def test_session_tampering_and_expiration(self):
        """Tampered or expired session tokens must be rejected."""
        valid_token = SessionService.create_session({
            "id": 1,
            "email": "session@alumni.istanbul.edu.tr",
            "name": "Session User",
            "role": "alumnus",
        })
        self.assertIsNotNone(SessionService.get_session(valid_token))

        # Tampered signature
        tampered_token = valid_token[:-4] + "ffff"
        self.assertIsNone(SessionService.get_session(tampered_token))

        # Expired session
        expired_token = SessionService.create_session(
            {"id": 2, "email": "exp@alumni.istanbul.edu.tr", "name": "Exp", "role": "alumnus"},
            max_age_seconds=-1,
        )
        self.assertIsNone(SessionService.get_session(expired_token))

    def test_protected_routes_unauthenticated(self):
        """Protected routes without session cookie must deny access."""
        # HTML dashboard redirects to login
        status_code, headers, _ = self._run_request("GET", "/dashboard")
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))

        # JSON api/me returns HTTP 401
        status_code, _, data = self._run_request(
            "GET",
            "/api/me",
            headers={"accept": "application/json"},
        )
        self.assertEqual(status_code, 401)
        self.assertIn("detail", data)

    def test_protected_routes_authenticated(self):
        """Protected routes with valid session cookie grant access."""
        user = self._create_test_user(
            name="Zeynep Kaya",
            email="zeynep@alumni.istanbul.edu.tr",
        )
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        # HTML dashboard returns 200 and renders user name
        status_code, _, body = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)
        self.assertIn("Zeynep Kaya", body)
        self.assertIn("Mezun Portalı", body)

        # JSON /api/me returns 200 and profile
        status_code, _, data = self._run_request("GET", "/api/me", cookies=cookies)
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["user"]["email"], "zeynep@alumni.istanbul.edu.tr")

    def test_role_enforcement_and_admin_guard(self):
        """Role-guarded endpoint allows admin and forbids alumnus (HTTP 403)."""
        # User 1: Regular alumnus
        alumnus = self._create_test_user(email="alumnus@alumni.istanbul.edu.tr", role="alumnus")
        alumnus_token = SessionService.create_session(alumnus)

        status_code, _, data = self._run_request(
            "GET",
            "/api/admin/overview",
            cookies={settings.SESSION_COOKIE_NAME: alumnus_token},
        )
        self.assertEqual(status_code, 403)
        self.assertIn("yetkiniz bulunmamaktadır", data.get("detail", ""))

        # User 2: Administrator
        admin = self._create_test_user(email="admin@alumni.istanbul.edu.tr", role="admin")
        admin_token = SessionService.create_session(admin)

        status_code, _, data = self._run_request(
            "GET",
            "/api/admin/overview",
            cookies={settings.SESSION_COOKIE_NAME: admin_token},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["admin"]["role"], "admin")

    def test_prevent_role_tampering_during_login(self):
        """Client sending role='admin' in payload cannot elevate role if database has 'alumnus'."""
        self._create_test_user(email="normal@alumni.istanbul.edu.tr", role="alumnus")
        payload = {
            "email": "normal@alumni.istanbul.edu.tr",
            "password": "Password123!",
            "role": "admin",
            "is_admin": True,
        }
        status_code, res_headers, data = self._run_request(
            "POST",
            "/api/login",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data["data"]["role"], "alumnus")

        set_cookie = res_headers.get("set-cookie", "")
        token = set_cookie.split(";")[0].split("=")[1]
        session = SessionService.get_session(token)
        self.assertEqual(session["role"], "alumnus")

    def test_production_secret_key_validation(self):
        """Settings must fail safely in production if SECRET_KEY is missing, predictable, or too weak."""
        from app.core.config import Settings

        # Default key fails in production
        with self.assertRaises(ValueError) as ctx:
            Settings(APP_ENV="production")
        self.assertIn("CRITICAL SECURITY CONFIGURATION ERROR", str(ctx.exception))

        # Predictable fallback fails in production
        with self.assertRaises(ValueError) as ctx:
            Settings(
                APP_ENV="production",
                SECRET_KEY="alumni-tracking-system-super-secret-key-2026",
            )
        self.assertIn("predictable fallback", str(ctx.exception).lower())

        # Weak/short key (< 32 chars) fails in production
        with self.assertRaises(ValueError) as ctx:
            Settings(
                APP_ENV="production",
                SECRET_KEY="short-secret-key",
            )
        self.assertIn("at least 32 characters", str(ctx.exception).lower())

        # Strong key (>= 32 chars) passes in production
        strong_key = "a" * 32
        prod_settings = Settings(APP_ENV="production", SECRET_KEY=strong_key)
        self.assertTrue(prod_settings.is_production)
        self.assertTrue(prod_settings.session_cookie_secure)

    def test_hmac_full_64_character_signature_and_constant_time(self):
        """Session token must use full 64-hex-character HMAC-SHA256 signature and constant-time check."""
        user = self._create_test_user(email="sign_check@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)

        self.assertIn(".", token)
        raw_id, signature = token.split(".", 1)
        # 64 hex characters = 256 bits HMAC-SHA256
        self.assertEqual(len(signature), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in signature))

        # Valid token extracts raw_id
        extracted_id = SessionService._verify_and_extract_raw_id(token)
        self.assertEqual(extracted_id, raw_id)

        # Truncated or modified signature fails
        self.assertIsNone(SessionService._verify_and_extract_raw_id(f"{raw_id}.{signature[:16]}"))
        flipped_signature = signature[:-1] + ("0" if signature[-1] != "0" else "1")
        self.assertIsNone(SessionService._verify_and_extract_raw_id(f"{raw_id}.{flipped_signature}"))

        # Malformed tokens fail safely
        self.assertIsNone(SessionService._verify_and_extract_raw_id(""))
        self.assertIsNone(SessionService._verify_and_extract_raw_id("invalid-token-without-dot"))
        self.assertIsNone(SessionService._verify_and_extract_raw_id("."))

    def test_expired_and_deleted_sessions_rejected_by_routes(self):
        """Expired or deleted sessions must immediately be rejected by protected routes."""
        user = self._create_test_user(email="reject_test@alumni.istanbul.edu.tr")
        token = SessionService.create_session(user)
        cookies = {settings.SESSION_COOKIE_NAME: token}

        # Session is valid initially
        status_code, _, data = self._run_request("GET", "/api/me", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Deleting session invalidates it immediately
        deleted = SessionService.delete_session(token)
        self.assertTrue(deleted)
        self.assertIsNone(SessionService.get_session(token))

        # Subsequent API call must return 401 Unauthorized
        status_code, _, data = self._run_request("GET", "/api/me", cookies=cookies)
        self.assertEqual(status_code, 401)

        # Subsequent Dashboard call must redirect to login
        status_code, headers, _ = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))

    def test_session_cookie_flags_and_properties(self):
        """Session cookies must enforce HttpOnly and SameSite=lax, with Secure in production."""
        from app.core.config import Settings

        dev_settings = Settings(APP_ENV="development")
        self.assertFalse(dev_settings.is_production)
        self.assertFalse(dev_settings.session_cookie_secure)

        # Explicit override
        override_settings = Settings(APP_ENV="development", SESSION_COOKIE_SECURE=True)
        self.assertTrue(override_settings.session_cookie_secure)

        # Cookie flags in response
        self._create_test_user(email="cookie_flags@alumni.istanbul.edu.tr", password="Password123!")
        payload = {
            "email": "cookie_flags@alumni.istanbul.edu.tr",
            "password": "Password123!",
        }
        _, headers, _ = self._run_request(
            "POST",
            "/api/login",
            body=payload,
            headers={"content-type": "application/json"},
        )
        set_cookie = headers.get("set-cookie", "")
        self.assertIn("httponly", set_cookie.lower())
        self.assertIn("samesite=lax", set_cookie.lower())
        self.assertIn("path=/", set_cookie.lower())

    def test_cookie_authenticated_state_changing_requires_csrf(self):
        """Cookie-authenticated state-changing requests must be rejected without valid CSRF token."""
        user = self._create_test_user(email="auth_csrf@alumni.istanbul.edu.tr", role="admin")
        token = SessionService.create_session(user)
        session = SessionService.get_session(token)
        csrf_token = session["csrf_token"]

        cookies = {settings.SESSION_COOKIE_NAME: token}

        # 1. State-changing POST without CSRF token -> 403 Forbidden
        status_code, _, data = self._run_request(
            "POST",
            "/api/users",
            body={"name": "New User", "email": "new@alumni.istanbul.edu.tr", "department": "CS", "graduation_year": 2022},
            headers={"content-type": "application/json", "accept": "application/json"},
            cookies=cookies,
        )
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF doğrulaması başarısız", data.get("message", ""))

        # 2. State-changing POST with invalid CSRF token -> 403 Forbidden
        status_code, _, data = self._run_request(
            "POST",
            "/api/users",
            body={"name": "New User", "email": "new@alumni.istanbul.edu.tr", "department": "CS", "graduation_year": 2022},
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "x-csrf-token": "completely_wrong_csrf_token",
            },
            cookies=cookies,
        )
        self.assertEqual(status_code, 403)
        self.assertIn("CSRF doğrulaması başarısız", data.get("message", ""))

        # 3. State-changing POST with valid X-CSRF-Token -> 201 Created
        status_code, _, data = self._run_request(
            "POST",
            "/api/users",
            body={"name": "New User", "email": "new@alumni.istanbul.edu.tr", "department": "CS", "graduation_year": 2022},
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "x-csrf-token": csrf_token,
            },
            cookies=cookies,
        )
        self.assertEqual(status_code, 201)

    def test_csrf_origin_header_validation(self):
        """Requests with untrusted Origin or Referer headers must be rejected with HTTP 403."""
        # Untrusted Origin on POST
        status_code, _, data = self._run_request(
            "POST",
            "/api/login",
            body={"email": "any@alumni.istanbul.edu.tr", "password": "Password123!"},
            headers={
                "content-type": "application/json",
                "origin": "http://evil.com",
            },
        )
        self.assertEqual(status_code, 403)
        self.assertIn("Untrusted Origin", data.get("message", ""))

        # Untrusted Referer on POST
        status_code, _, data = self._run_request(
            "POST",
            "/api/login",
            body={"email": "any@alumni.istanbul.edu.tr", "password": "Password123!"},
            headers={
                "content-type": "application/json",
                "referer": "http://malicious-site.org/phishing",
            },
        )
        self.assertEqual(status_code, 403)
        self.assertIn("Untrusted Referer", data.get("message", ""))

        # Trusted Origin -> proceeds to authentication check
        self._create_test_user(email="origin_test@alumni.istanbul.edu.tr", password="CorrectPass123")
        status_code, _, data = self._run_request(
            "POST",
            "/api/login",
            body={"email": "origin_test@alumni.istanbul.edu.tr", "password": "CorrectPass123"},
            headers={
                "content-type": "application/json",
                "origin": "http://localhost:8000",
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("status"), "success")


if __name__ == "__main__":
    unittest.main()
