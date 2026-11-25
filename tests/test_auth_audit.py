"""Security audit test suite validating:

1. Bearer token authentication (cryptographic validation, rejection of invalid/expired/revoked tokens,
   and verification that CSRF bypass for Bearer requests does not bypass AuthN or AuthZ).
2. Academician and admin authorization (announcement create/update/delete permissions, exact permissions
   of admin vs academician vs ordinary alumnus, ownership enforcement preventing ID manipulation,
   and dynamic PostgreSQL role synchronization).
"""

import asyncio
from datetime import datetime, timedelta
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password
from app.main import app
from app.models.application import ApplicationDB
from app.models.job_posting import JobPostingDB
from app.models.user_db import UserDB
from app.services.announcement_service import AnnouncementService, clear_announcements
from app.services.session_service import SessionService, clear_sessions
from app.services.user_service import clear_users


class TestAuthAudit(unittest.TestCase):
    """Verifies route protection rules, Bearer token security, and role/ownership checks."""

    @classmethod
    def setUpClass(cls):
        clear_users()
        clear_announcements()
        clear_sessions()

    def setUp(self):
        clear_users()
        clear_announcements()
        clear_sessions()

        with get_db_session() as db:
            db.query(ApplicationDB).delete()
            db.query(JobPostingDB).delete()
            db.query(UserDB).delete()

            # 1. Ordinary Alumnus User A
            user_a = UserDB(
                name="Alumnus User A",
                email="user_a@alumni.istanbul.edu.tr",
                department="Bilgisayar",
                graduation_year=2021,
                hashed_password=hash_password("Password123!"),
                role="alumnus",
                created_at=datetime.utcnow(),
            )
            # 2. Academician User B (Author of Announcement B)
            user_b = UserDB(
                name="Prof. Dr. Academician B",
                email="academician_b@istanbul.edu.tr",
                department="Bilgisayar",
                graduation_year=2005,
                hashed_password=hash_password("ProfPass123!"),
                role="academician",
                created_at=datetime.utcnow(),
            )
            # 3. Academician User C (Peer Academician, NOT Author of Announcement B)
            user_c = UserDB(
                name="Doç. Dr. Academician C",
                email="academician_c@istanbul.edu.tr",
                department="Endüstri",
                graduation_year=2010,
                hashed_password=hash_password("ProfPass456!"),
                role="academician",
                created_at=datetime.utcnow(),
            )
            # 4. Administrator
            admin = UserDB(
                name="Admin User",
                email="admin@alumni.istanbul.edu.tr",
                department="Yönetim",
                graduation_year=2015,
                hashed_password=hash_password("AdminPass123!"),
                role="admin",
                created_at=datetime.utcnow(),
            )
            db.add_all([user_a, user_b, user_c, admin])
            db.flush()

            self.user_a_id = user_a.id
            self.user_b_id = user_b.id
            self.user_c_id = user_c.id
            self.admin_id = admin.id

            job = JobPostingDB(
                id=1,
                title="Yazılım Mühendisi",
                company_name="Tech Corp",
                location="İstanbul",
                description="Python geliştirici aranıyor.",
                created_at=datetime.utcnow(),
            )
            db.add(job)
            db.flush()

            app_b = ApplicationDB(
                id=1,
                user_id=self.user_b_id,
                job_posting_id=1,
                status="applied",
                created_at=datetime.utcnow(),
            )
            db.add(app_b)
            db.flush()

        # Create sessions
        self.user_a_token = SessionService.create_session({
            "id": self.user_a_id,
            "name": "Alumnus User A",
            "email": "user_a@alumni.istanbul.edu.tr",
            "role": "alumnus",
        })
        self.user_b_token = SessionService.create_session({
            "id": self.user_b_id,
            "name": "Prof. Dr. Academician B",
            "email": "academician_b@istanbul.edu.tr",
            "role": "academician",
        })
        self.user_c_token = SessionService.create_session({
            "id": self.user_c_id,
            "name": "Doç. Dr. Academician C",
            "email": "academician_c@istanbul.edu.tr",
            "role": "academician",
        })
        self.admin_token = SessionService.create_session({
            "id": self.admin_id,
            "name": "Admin User",
            "email": "admin@alumni.istanbul.edu.tr",
            "role": "admin",
        })

        # Create an announcement authored by Academician User B
        ann_b = AnnouncementService.create_announcement({
            "title": "Bölüm Semineri",
            "content": "Akademik yıl açılış semineri.",
            "author": "Prof. Dr. Academician B",
            "created_by": self.user_b_id,
        })
        self.announcement_b_id = ann_b.id

    def tearDown(self):
        clear_users()
        clear_announcements()
        clear_sessions()
        with get_db_session() as db:
            db.query(ApplicationDB).delete()
            db.query(JobPostingDB).delete()
            db.query(UserDB).delete()

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
                        response_headers[key] = val
                elif message["type"] == "http.response.body":
                    response_chunks.append(message.get("body", b""))

            await app(scope, receive, send)

            raw_body = b"".join(response_chunks).decode("utf-8")
            parsed_body = raw_body
            if "application/json" in response_headers.get("content-type", ""):
                try:
                    parsed_body = json.loads(raw_body)
                except Exception:
                    pass

            return status_code[0], response_headers, parsed_body

        return asyncio.run(_asgi_call())

    # =========================================================================
    # 1. Genuinely Public Endpoints (Accessible Without Authentication)
    # =========================================================================

    def test_public_pages_accessible_unauthenticated(self):
        """Home, about, login, register, health, and public directory pages return 200."""
        public_urls = ["/", "/about", "/login", "/register", "/api/health", "/jobs", "/announcements", "/users"]
        for url in public_urls:
            code, _, _ = self._run_request("GET", url)
            self.assertEqual(code, 200, f"Expected 200 for public url {url}, got {code}")

    # =========================================================================
    # 2. Unauthenticated Write Operations (Must Return 401 API / 303 Web)
    # =========================================================================

    def test_unauthenticated_api_write_rejected_with_401(self):
        """All state-changing API endpoints must return 401 when unauthenticated."""
        unauthenticated_calls = [
            ("POST", "/api/users", {"name": "Test", "email": "x@alumni.test", "department": "CS", "graduation_year": 2020}),
            ("PUT", f"/api/users/{self.user_a_id}", {"name": "Test", "email": "x@alumni.test", "department": "CS", "graduation_year": 2020}),
            ("PATCH", f"/api/users/{self.user_a_id}", {"name": "Test"}),
            ("DELETE", f"/api/users/{self.user_a_id}", None),
            ("POST", "/api/job-postings", {"title": "New Job", "company_name": "Co", "location": "Remote", "description": "Desc"}),
            ("PUT", "/api/job-postings/1", {"title": "Updated", "company_name": "Co", "location": "Remote", "description": "Desc"}),
            ("PATCH", "/api/job-postings/1", {"title": "Updated"}),
            ("DELETE", "/api/job-postings/1", None),
            ("POST", "/api/applications", {"user_id": self.user_a_id, "job_posting_id": 1}),
            ("PATCH", "/api/applications/1", {"status": "accepted"}),
            ("DELETE", "/api/applications/1", None),
            ("POST", "/api/announcements", {"title": "Ann", "content": "Body", "author": "Anon"}),
            ("PUT", f"/api/announcements/{self.announcement_b_id}", {"title": "Ann", "content": "Body", "author": "Anon"}),
            ("PATCH", f"/api/announcements/{self.announcement_b_id}", {"title": "Updated"}),
            ("DELETE", f"/api/announcements/{self.announcement_b_id}", None),
        ]
        for method, path, body in unauthenticated_calls:
            code, _, data = self._run_request(method, path, body=body, headers={"accept": "application/json"})
            self.assertEqual(code, 401, f"{method} {path} should return 401 for unauthenticated request, got {code}")

    def test_unauthenticated_web_write_redirects_to_login(self):
        """State-changing web endpoints must redirect unauthenticated requests to /login."""
        web_writes = [
            ("POST", "/users", {"name": "Test", "email": "x@alumni.test", "department": "CS", "graduation_year": "2020"}),
            ("POST", f"/users/{self.user_a_id}/edit", {"name": "Test", "email": "x@alumni.test", "department": "CS", "graduation_year": "2020"}),
            ("POST", f"/users/{self.user_a_id}/delete", {}),
            ("POST", "/jobs/1/apply", {}),
            ("POST", "/announcements", {"title": "Title", "content": "Content", "author": "Author"}),
            ("POST", f"/announcements/{self.announcement_b_id}/edit", {"title": "Title", "content": "Content", "author": "Author"}),
            ("POST", f"/announcements/{self.announcement_b_id}/delete", {}),
        ]
        for method, path, body in web_writes:
            code, headers, _ = self._run_request(
                method,
                path,
                body=body,
                headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
            )
            self.assertEqual(code, 303, f"{method} {path} should redirect with 303, got {code}")
            self.assertIn("/login", headers.get("location", ""))

    # =========================================================================
    # 3. Unauthenticated Private GET Routes (Must Return 401 API / 303 Web)
    # =========================================================================

    def test_unauthenticated_private_get_routes_protected(self):
        """Private views and endpoints return 401 for API and 303 for Web when unauthenticated."""
        private_api_gets = [
            "/api/applications",
            f"/api/users/{self.user_a_id}/applications",
            "/api/job-postings/1/applications",
            "/api/me",
        ]
        for url in private_api_gets:
            code, _, _ = self._run_request("GET", url, headers={"accept": "application/json"})
            self.assertEqual(code, 401, f"GET {url} should return 401 unauthenticated, got {code}")

        private_web_gets = [
            "/applications",
            "/jobs/1/apply",
            f"/users/{self.user_a_id}/edit",
            f"/announcements/{self.announcement_b_id}/edit",
            "/dashboard",
        ]
        for url in private_web_gets:
            code, headers, _ = self._run_request("GET", url, headers={"accept": "text/html"})
            self.assertEqual(code, 303, f"GET {url} should redirect unauthenticated, got {code}")
            self.assertIn("/login", headers.get("location", ""))

    # =========================================================================
    # 4. Bearer Token Authentication Verification
    # =========================================================================

    def test_bearer_token_cryptographically_validated_and_accepted(self):
        """Valid Authorization: Bearer token is accepted and loads correct user."""
        code, headers, data = self._run_request(
            "GET",
            "/api/me",
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 200)
        user_info = data.get("user", {})
        self.assertEqual(user_info.get("email"), "user_a@alumni.istanbul.edu.tr")
        self.assertEqual(user_info.get("role"), "alumnus")

    def test_bearer_token_tampered_signature_rejected_with_401(self):
        """Bearer token with modified raw_id or invalid HMAC signature is rejected with HTTP 401."""
        tampered_token = self.user_a_token[:-4] + "ffff"
        code, headers, data = self._run_request(
            "GET",
            "/api/me",
            headers={"authorization": f"Bearer {tampered_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 401)
        self.assertIn("bearer", headers.get("www-authenticate", "").lower())

    def test_bearer_token_malformed_rejected_with_401(self):
        """Malformed, unsigned, or empty Bearer token is rejected with HTTP 401."""
        for bad_token in ["not_a_valid_token", "randomstringwithoutdot", ""]:
            code, headers, data = self._run_request(
                "GET",
                "/api/me",
                headers={"authorization": f"Bearer {bad_token}".strip(), "accept": "application/json"},
            )
            self.assertEqual(code, 401, f"Token '{bad_token}' must return 401")
            self.assertIn("bearer", headers.get("www-authenticate", "").lower())

    def test_bearer_token_expired_rejected_with_401(self):
        """Expired Bearer token is rejected with HTTP 401."""
        # Create an immediately expired token
        expired_token = SessionService.create_session(
            {"id": self.user_a_id, "email": "user_a@alumni.istanbul.edu.tr", "name": "A", "role": "alumnus"},
            max_age_seconds=-10,
        )
        code, headers, data = self._run_request(
            "GET",
            "/api/me",
            headers={"authorization": f"Bearer {expired_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 401)
        self.assertIn("bearer", headers.get("www-authenticate", "").lower())

    def test_bearer_token_revoked_rejected_with_401(self):
        """Revoked/deleted session Bearer token is rejected with HTTP 401."""
        token_to_revoke = SessionService.create_session(
            {"id": self.user_a_id, "email": "user_a@alumni.istanbul.edu.tr", "name": "A", "role": "alumnus"}
        )
        # Session is valid initially
        code, _, _ = self._run_request("GET", "/api/me", headers={"authorization": f"Bearer {token_to_revoke}"})
        self.assertEqual(code, 200)

        # Revoke/delete the session
        SessionService.delete_session(token_to_revoke)

        # Subsequent request with revoked token must return 401
        code, headers, _ = self._run_request("GET", "/api/me", headers={"authorization": f"Bearer {token_to_revoke}"})
        self.assertEqual(code, 401)
        self.assertIn("bearer", headers.get("www-authenticate", "").lower())

    def test_bearer_token_on_public_route_with_invalid_token_rejected_with_401(self):
        """Supplying an invalid Bearer token to a public route returns 401 instead of anonymous 200."""
        code, headers, _ = self._run_request(
            "GET",
            "/jobs",
            headers={"authorization": "Bearer invalid_or_tampered_token", "accept": "application/json"},
        )
        self.assertEqual(code, 401)
        self.assertIn("bearer", headers.get("www-authenticate", "").lower())

    def test_bearer_csrf_bypass_does_not_bypass_authentication_or_authorization(self):
        """Bypassing CSRF for Bearer token requests strictly preserves AuthN and AuthZ enforcement."""
        # 1. State-changing POST with valid Admin Bearer token succeeds without CSRF header
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Senior Engineer", "company_name": "Acme Inc", "location": "Remote"},
            headers={"authorization": f"Bearer {self.admin_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 201)

        # 2. State-changing POST with invalid Bearer token is rejected with 401 (AuthN enforced)
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Senior Engineer", "company_name": "Acme Inc", "location": "Remote"},
            headers={"authorization": "Bearer forged_invalid_token", "accept": "application/json"},
        )
        self.assertEqual(code, 401)

        # 3. State-changing POST with valid Alumnus Bearer token is rejected with 403 (AuthZ enforced)
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Senior Engineer", "company_name": "Acme Inc", "location": "Remote"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

        # 4. Cookie request carrying an Authorization: Bearer header cannot bypass CSRF check
        code, _, data = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Senior Engineer", "company_name": "Acme Inc", "location": "Remote"},
            headers={"authorization": f"Bearer {self.admin_token}", "accept": "application/json"},
            cookies={settings.SESSION_COOKIE_NAME: self.admin_token},  # Cookie present but NO x-csrf-token
        )
        self.assertEqual(code, 403)
        self.assertIn("CSRF doğrulaması başarısız", data.get("message", ""))

    # =========================================================================
    # 5. Academician and Admin Authorization & Announcement Permissions Matrix
    # =========================================================================

    def test_announcement_permissions_matrix(self):
        """Verifies exact permissions across Admin, Academician, and Ordinary Users:

        - Alumnus: cannot create, update, or delete announcements (403 Forbidden).
        - Academician: can create; can update/delete own announcements; cannot update/delete others (403).
        - Admin: full moderation rights over all announcements.
        """
        # A) Ordinary user (alumnus) cannot create announcements
        code, _, _ = self._run_request(
            "POST",
            "/api/announcements",
            body={"title": "Alumnus Post", "content": "Hello", "author": "Alumnus A"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403, "Ordinary alumnus creating announcement via API must return 403")

        code, _, _ = self._run_request(
            "POST",
            "/announcements",
            body={"title": "Alumnus Post", "content": "Hello", "author": "Alumnus A"},
            headers={
                "authorization": f"Bearer {self.user_a_token}",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html",
            },
        )
        self.assertEqual(code, 403, "Ordinary alumnus creating announcement via web must return 403")

        # B) Academician B can create announcements (auto-assigned created_by = user_b_id)
        code, _, new_ann = self._run_request(
            "POST",
            "/api/announcements",
            body={"title": "Akademik Duyuru", "content": "Vize takvimi açıklandı.", "author": "Prof. B"},
            headers={"authorization": f"Bearer {self.user_b_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 201)
        created_id = new_ann["data"]["id"]
        self.assertEqual(new_ann["data"]["created_by"], self.user_b_id)

        # C) Academician B can update their own announcement
        code, _, _ = self._run_request(
            "PUT",
            f"/api/announcements/{created_id}",
            body={"title": "Güncellenmiş Vize Takvimi", "content": "Yeni tarihler.", "author": "Prof. B"},
            headers={"authorization": f"Bearer {self.user_b_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 200)

        # D) Academician C (another academician) CANNOT update Academician B's announcement
        code, _, _ = self._run_request(
            "PUT",
            f"/api/announcements/{created_id}",
            body={"title": "Tampered", "content": "Tampered", "author": "Prof. C"},
            headers={"authorization": f"Bearer {self.user_c_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403, "Academician C updating Academician B's announcement must return 403")

        # E) Academician C CANNOT delete Academician B's announcement
        code, _, _ = self._run_request(
            "DELETE",
            f"/api/announcements/{created_id}",
            headers={"authorization": f"Bearer {self.user_c_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403, "Academician C deleting Academician B's announcement must return 403")

        # F) Ordinary user A CANNOT update or delete Academician B's announcement
        code, _, _ = self._run_request(
            "PUT",
            f"/api/announcements/{created_id}",
            body={"title": "Hacked", "content": "Hacked", "author": "Alumnus A"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403, "Alumnus updating announcement must return 403")

        code, _, _ = self._run_request(
            "DELETE",
            f"/api/announcements/{created_id}",
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403, "Alumnus deleting announcement must return 403")

        # G) Admin CAN update any announcement
        code, _, _ = self._run_request(
            "PUT",
            f"/api/announcements/{created_id}",
            body={"title": "Admin Modere Etti", "content": "İçerik onaylandı.", "author": "Yönetim"},
            headers={"authorization": f"Bearer {self.admin_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 200)

        # H) Admin CAN delete any announcement
        code, _, _ = self._run_request(
            "DELETE",
            f"/api/announcements/{created_id}",
            headers={"authorization": f"Bearer {self.admin_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 200)

    # =========================================================================
    # 6. Resource ID Manipulation & Ownership Bypass Prevention
    # =========================================================================

    def test_ownership_cannot_be_bypassed_by_changing_resource_ids(self):
        """Attackers cannot access or tamper with resources by manipulating path IDs or payloads."""
        # 1. Academician C trying to update Academician B's announcement by targeting its ID
        code, _, _ = self._run_request(
            "PUT",
            f"/api/announcements/{self.announcement_b_id}",
            body={"title": "Stolen", "content": "Stolen", "author": "Prof. C"},
            headers={"authorization": f"Bearer {self.user_c_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

        # 2. Non-existent announcement ID returns 404 for academician
        code, _, _ = self._run_request(
            "PUT",
            "/api/announcements/99999",
            body={"title": "Ghost", "content": "Ghost", "author": "Prof. B"},
            headers={"authorization": f"Bearer {self.user_b_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 404)

        # 3. Ownership transfer via payload injection (sending created_by: admin_id) is stripped
        code, _, updated = self._run_request(
            "PUT",
            f"/api/announcements/{self.announcement_b_id}",
            body={"title": "Updated", "content": "Updated", "created_by": self.admin_id},
            headers={"authorization": f"Bearer {self.user_b_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 200)
        self.assertEqual(
            updated["data"]["created_by"],
            self.user_b_id,
            "Non-admin cannot reassign announcement created_by ownership",
        )

        # 4. User A attempting to modify User B's profile via path ID
        code, _, _ = self._run_request(
            "PUT",
            f"/api/users/{self.user_b_id}",
            body={"name": "Hacked", "email": "user_b@alumni.istanbul.edu.tr", "department": "CS", "graduation_year": 2020},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

        # 5. User A attempting to view User B's applications via path ID
        code, _, _ = self._run_request(
            "GET",
            f"/api/users/{self.user_b_id}/applications",
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

    # =========================================================================
    # 7. Dynamic Role Synchronization from Database
    # =========================================================================

    def test_role_values_always_come_from_database(self):
        """User role permissions are dynamically synchronized from PostgreSQL, preventing role tampering."""
        # User A is currently alumnus: cannot create job postings
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Job", "company_name": "Co", "location": "Remote"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

        # Promote User A directly in PostgreSQL to 'admin'
        with get_db_session() as db:
            user_db = db.query(UserDB).filter(UserDB.id == self.user_a_id).first()
            user_db.role = "admin"
            db.flush()

        # Next immediate request with existing token automatically inherits admin permissions
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Job Promoted", "company_name": "Co", "location": "Remote"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 201)

        # Demote User A back to 'alumnus' in PostgreSQL
        with get_db_session() as db:
            user_db = db.query(UserDB).filter(UserDB.id == self.user_a_id).first()
            user_db.role = "alumnus"
            db.flush()

        # Next request immediately loses admin privileges
        code, _, _ = self._run_request(
            "POST",
            "/api/job-postings",
            body={"title": "Job Demoted", "company_name": "Co", "location": "Remote"},
            headers={"authorization": f"Bearer {self.user_a_token}", "accept": "application/json"},
        )
        self.assertEqual(code, 403)

    # =========================================================================
    # 8. Web Form Safe Binding
    # =========================================================================

    def test_web_apply_safely_binds_to_authenticated_session(self):
        """Web POST /jobs/{id}/apply binds application to logged-in user and creates DB record."""
        code, headers, body = self._run_request(
            "POST",
            "/jobs/1/apply",
            body={},
            headers={
                "authorization": f"Bearer {self.user_a_token}",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html",
            },
        )
        self.assertEqual(code, 200)
        self.assertIn("Başvurunuz başarıyla kaydedildi!", body)

        with get_db_session() as db:
            user_a_app = db.query(ApplicationDB).filter(
                ApplicationDB.user_id == self.user_a_id,
                ApplicationDB.job_posting_id == 1,
            ).first()
            self.assertIsNotNone(user_a_app, "Application was not created for authenticated user_a")
            self.assertEqual(user_a_app.status, "pending")


if __name__ == "__main__":
    unittest.main()
