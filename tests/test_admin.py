"""Comprehensive test suite for Admin Panel and Initial Admin Account Setup.

Covers:
1. Initial admin bootstrap script and service functionality (safe, idempotent, user-not-found error, password intact).
2. Admin route protection (unauthenticated -> 303 redirect, non-admin -> 403 forbidden, admin -> 200 ok).
3. Dashboard real database statistics calculation.
4. User management: listing, search, role filtering, pagination.
5. Role assignment and user editing.
6. Self-deletion protection guard.
7. Last admin protection guards (both deletion and demotion).
8. Job postings administrative CRUD operations.
9. Candidate applications review and status management.
10. Announcements administrative CRUD operations.
11. CSRF token validation across state-changing admin actions.
12. Password hash security (never exposed in contexts or responses).
"""

import asyncio
from datetime import datetime
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.announcement import AnnouncementDB
from app.models.application import ApplicationDB
from app.models.job_posting import JobPostingDB
from app.models.user_db import UserDB
from app.services.admin_service import AdminService
from app.services.session_service import SessionService, clear_sessions
from app.services.user_service import UserService, clear_users
from scripts.bootstrap_admin import bootstrap_admin


class TestAdminPanel(unittest.TestCase):
    """Test suite verifying all Admin Panel and Bootstrap requirements."""

    def setUp(self):
        """Clean database and in-memory stores before each test."""
        clear_users()
        clear_sessions()
        with get_db_session() as db:
            db.query(ApplicationDB).delete()
            db.query(AnnouncementDB).delete()
            db.query(JobPostingDB).delete()
            db.query(UserDB).delete()

    def tearDown(self):
        """Clean database and in-memory stores after each test."""
        clear_users()
        clear_sessions()
        with get_db_session() as db:
            db.query(ApplicationDB).delete()
            db.query(AnnouncementDB).delete()
            db.query(JobPostingDB).delete()
            db.query(UserDB).delete()

    def _create_user(
        self,
        name: str = "Test User",
        email: str = "test@example.com",
        password: str = "SecurePass123!",
        role: str = "alumnus",
        department: str = "Bilgisayar Mühendisliği",
        graduation_year: int = 2020,
    ) -> Dict[str, Any]:
        """Creates and stores a test user in PostgreSQL and mirrors in UserService."""
        hashed = hash_password(password)
        with get_db_session() as db:
            user = UserDB(
                name=name,
                email=email.strip().lower(),
                department=department,
                graduation_year=graduation_year,
                hashed_password=hashed,
                role=role,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.flush()
            user_data = {
                "id": user.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "graduation_year": user.graduation_year,
                "role": user.role,
                "hashed_password": user.hashed_password,
            }

        UserService.create_user(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            department=user_data["department"],
            graduation_year=user_data["graduation_year"],
            role=user_data["role"],
        )
        return user_data

    def _login_user(self, user_data: Dict[str, Any]) -> Tuple[str, Dict[str, str], str]:
        """Creates an authenticated session for user and returns (token, cookies, csrf_token)."""
        token = SessionService.create_session(user_data)
        session_info = SessionService.get_session(token)
        csrf_token = session_info.get("csrf_token") if session_info else ""
        cookies = {settings.SESSION_COOKIE_NAME: token}
        return token, cookies, csrf_token

    @staticmethod
    def _run_request(
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], Any]:
        """Dispatches an ASGI request directly to the FastAPI app."""
        async def _call():
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

            if "?" in path:
                req_path, qs_str = path.split("?", 1)
                qs_bytes = qs_str.encode("latin-1")
            else:
                req_path = path
                qs_bytes = b""

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": method.upper(),
                "path": req_path,
                "raw_path": req_path.encode("latin-1"),
                "query_string": qs_bytes,
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

            response_status = 200
            response_headers: Dict[str, str] = {}
            response_body = bytearray()

            async def send(message):
                nonlocal response_status, response_headers, response_body
                if message["type"] == "http.response.start":
                    response_status = message["status"]
                    for k, v in message.get("headers", []):
                        response_headers[k.decode("latin-1").lower()] = v.decode("latin-1")
                elif message["type"] == "http.response.body":
                    response_body.extend(message.get("body", b""))

            await app(scope, receive, send)

            raw_text = response_body.decode("utf-8", errors="replace")
            try:
                parsed_data = json.loads(raw_text)
            except Exception:
                parsed_data = raw_text

            return response_status, response_headers, parsed_data

        return asyncio.run(_call())

    # -------------------------------------------------------------------------
    # Initial Admin Bootstrap Tests
    # -------------------------------------------------------------------------
    def test_bootstrap_admin_user_not_found(self):
        """If target email doesn't exist, bootstrap reports clearly and creates no account."""
        target_email = "berentn05@gmail.com"
        result = AdminService.promote_user_to_admin(target_email)
        self.assertEqual(result["status"], "not_found")
        self.assertIn("not found in database", result["message"])
        self.assertIsNone(result["user"])

        # CLI exit code must be 1
        code = bootstrap_admin(target_email)
        self.assertEqual(code, 1)

        # Confirm no account was created in PostgreSQL
        with get_db_session() as db:
            user = db.query(UserDB).filter(UserDB.email == target_email).first()
            self.assertIsNone(user, "Bootstrap must NEVER create a user if not found")

    def test_bootstrap_admin_promotes_existing_user(self):
        """Bootstrap safely promotes an existing user to admin, preserving password and attributes."""
        target_email = "berentn05@gmail.com"
        raw_password = "MyComplexPassword2026!"
        created = self._create_user(
            name="Beren T.",
            email=target_email,
            password=raw_password,
            role="alumnus",
            department="Bilgisayar Mühendisliği",
            graduation_year=2024,
        )

        orig_hash = created["hashed_password"]

        # Run promotion
        result = AdminService.promote_user_to_admin(target_email)
        self.assertEqual(result["status"], "promoted")
        self.assertEqual(result["user"]["role"], "admin")

        # Verify DB record
        with get_db_session() as db:
            db_user = db.query(UserDB).filter(UserDB.email == target_email).first()
            self.assertIsNotNone(db_user)
            self.assertEqual(db_user.role, "admin")
            self.assertEqual(db_user.hashed_password, orig_hash, "Password hash must NOT be modified")
            self.assertTrue(verify_password(raw_password, db_user.hashed_password))

        # CLI exit code must be 0
        cli_code = bootstrap_admin(target_email)
        self.assertEqual(cli_code, 0)

    def test_bootstrap_admin_idempotent(self):
        """Repeated bootstrap executions on an already-admin user succeed without error or changes."""
        target_email = "berentn05@gmail.com"
        self._create_user(email=target_email, role="admin")

        result = AdminService.promote_user_to_admin(target_email)
        self.assertEqual(result["status"], "already_admin")
        self.assertEqual(result["user"]["role"], "admin")

        code = bootstrap_admin(target_email)
        self.assertEqual(code, 0)

    # -------------------------------------------------------------------------
    # Route Protection & Role Authorization Tests
    # -------------------------------------------------------------------------
    def test_admin_panel_unauthenticated_redirects_to_login(self):
        """Unauthenticated requests to /admin* must be redirected to /login with 303."""
        admin_paths = [
            "/admin",
            "/admin/users",
            "/admin/jobs",
            "/admin/applications",
            "/admin/announcements",
        ]
        for path in admin_paths:
            status_code, headers, _ = self._run_request(
                "GET", path, headers={"accept": "text/html"}
            )
            self.assertEqual(
                status_code,
                303,
                f"Unauthenticated web request to {path} must redirect with 303",
            )
            self.assertIn("/login", headers.get("location", ""))

    def test_admin_panel_non_admin_forbidden(self):
        """Non-admin authenticated roles (alumnus, student, academician) receive HTTP 403."""
        roles = ["alumnus", "student", "academician"]
        for role in roles:
            user = self._create_user(email=f"user_{role}@istanbul.edu.tr", role=role)
            _, cookies, _ = self._login_user(user)

            # Web request (text/html) -> 403 Forbidden with 403.html
            code, _, body = self._run_request(
                "GET", "/admin", cookies=cookies, headers={"accept": "text/html"}
            )
            self.assertEqual(code, 403, f"Role '{role}' accessing /admin must be 403")
            self.assertIn("403", body)
            self.assertIn("Erişim İzniniz Yok", body)

            # API request (application/json) -> 403 Forbidden with JSON
            code, _, data = self._run_request(
                "GET", "/admin", cookies=cookies, headers={"accept": "application/json"}
            )
            self.assertEqual(code, 403, f"Role '{role}' requesting /admin JSON must be 403")
            self.assertIn("yetkiniz bulunmamaktadır", data.get("detail", ""))

    def test_admin_panel_admin_access_allowed(self):
        """Authenticated admin can access all admin views with HTTP 200."""
        admin = self._create_user(email="admin@istanbul.edu.tr", role="admin")
        _, cookies, _ = self._login_user(admin)

        paths = [
            "/admin",
            "/admin/users",
            "/admin/jobs",
            "/admin/applications",
            "/admin/announcements",
        ]
        for path in paths:
            code, _, body = self._run_request(
                "GET", path, cookies=cookies, headers={"accept": "text/html"}
            )
            self.assertEqual(code, 200, f"Admin accessing {path} must return 200 OK")
            self.assertIn("Yönetim Paneli", body)

    # -------------------------------------------------------------------------
    # Dashboard Real Database Statistics Tests
    # -------------------------------------------------------------------------
    def test_admin_dashboard_real_statistics(self):
        """Admin dashboard aggregates and returns accurate real-time PostgreSQL metrics."""
        admin = self._create_user(email="admin_stats@istanbul.edu.tr", role="admin")
        self._create_user(email="alumni1@istanbul.edu.tr", role="alumnus")
        self._create_user(email="alumni2@istanbul.edu.tr", role="alumnus")
        self._create_user(email="student1@istanbul.edu.tr", role="student")
        self._create_user(email="prof1@istanbul.edu.tr", role="academician")

        # Seed 2 job postings
        with get_db_session() as db:
            j1 = JobPostingDB(title="Dev 1", company_name="Tech A")
            j2 = JobPostingDB(title="Dev 2", company_name="Tech B")
            db.add_all([j1, j2])
            db.flush()

            # Seed 1 application
            app1 = ApplicationDB(user_id=admin["id"], job_posting_id=j1.id, status="pending")
            db.add(app1)

            # Seed 1 announcement
            ann1 = AnnouncementDB(title="Duyuru 1", content="İçerik", created_by=admin["id"])
            db.add(ann1)

        stats = AdminService.get_system_stats()
        self.assertEqual(stats["total_users"], 5)
        self.assertEqual(stats["alumni_count"], 2)
        self.assertEqual(stats["students_count"], 1)
        self.assertEqual(stats["academicians_count"], 1)
        self.assertEqual(stats["admins_count"], 1)
        self.assertEqual(stats["jobs_count"], 2)
        self.assertEqual(stats["applications_count"], 1)
        self.assertEqual(stats["announcements_count"], 1)

        # Access dashboard as admin
        _, cookies, _ = self._login_user(admin)
        code, _, data = self._run_request(
            "GET", "/admin", cookies=cookies, headers={"accept": "application/json"}
        )
        self.assertEqual(code, 200)
        self.assertEqual(data["stats"]["total_users"], 5)
        self.assertEqual(data["stats"]["jobs_count"], 2)

    # -------------------------------------------------------------------------
    # User Management, Search & Filter Tests
    # -------------------------------------------------------------------------
    def test_admin_users_search_and_filter(self):
        """Searching users by name/email/department and filtering by role works accurately."""
        admin = self._create_user(email="admin_users@istanbul.edu.tr", role="admin")
        u1 = self._create_user(
            name="Zeynep Kaya", email="zeynep@alumni.edu", role="alumnus", department="Hukuk Fakültesi"
        )
        u2 = self._create_user(
            name="Caner Yıldız", email="caner@student.edu", role="student", department="Tıp Fakültesi"
        )
        u3 = self._create_user(
            name="Prof. Dr. Ahmet Bilge",
            email="ahmet@academic.edu",
            role="academician",
            department="Mühendislik Fakültesi",
        )

        _, cookies, _ = self._login_user(admin)

        # 1. Search by name
        res = AdminService.list_users(search="Zeynep")
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["users"][0]["name"], "Zeynep Kaya")

        # 2. Search by department
        res = AdminService.list_users(search="Mühendislik")
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["users"][0]["email"], "ahmet@academic.edu")

        # 3. Filter by role
        res = AdminService.list_users(role="student")
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["users"][0]["name"], "Caner Yıldız")

        # 4. Via HTTP GET /admin/users
        code, _, data = self._run_request(
            "GET",
            "/admin/users?role=academician",
            cookies=cookies,
            headers={"accept": "application/json"},
        )
        self.assertEqual(code, 200)
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["users"][0]["role"], "academician")

    # -------------------------------------------------------------------------
    # Role Assignment & Safety Protection Tests
    # -------------------------------------------------------------------------
    def test_admin_role_assignment(self):
        """Admin can assign roles (student, academician, alumnus, admin) to users."""
        admin = self._create_user(email="admin1@istanbul.edu.tr", role="admin")
        user = self._create_user(email="student_to_promote@istanbul.edu.tr", role="student")
        _, cookies, csrf_token = self._login_user(admin)

        # Promote user to academician
        code, _, data = self._run_request(
            "POST",
            f"/admin/users/{user['id']}/role",
            body={"role": "academician", "csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            updated = db.get(UserDB, user["id"])
            self.assertEqual(updated.role, "academician")

    def test_admin_self_deletion_prevented(self):
        """Admin cannot delete their own account (Self-Deletion Protection)."""
        admin = self._create_user(email="self_delete_admin@istanbul.edu.tr", role="admin")
        _, cookies, csrf_token = self._login_user(admin)

        # Attempt self-deletion
        code, _, data = self._run_request(
            "POST",
            f"/admin/users/{admin['id']}/delete",
            body={"csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 400, "Self deletion must be rejected with 400")
        self.assertIn("Kendi yönetici hesabınızı silemezsiniz", str(data))

    def test_admin_last_admin_deletion_prevented(self):
        """When only 1 admin exists, deleting that account is rejected (Last Admin Protection)."""
        admin1 = self._create_user(email="first_admin@istanbul.edu.tr", role="admin")
        admin2 = self._create_user(email="second_admin@istanbul.edu.tr", role="admin")
        _, cookies2, csrf2 = self._login_user(admin2)

        # Admin 2 deletes Admin 1 (allowed because 2 admins exist)
        code, _, _ = self._run_request(
            "POST",
            f"/admin/users/{admin1['id']}/delete",
            body={"csrf_token": csrf2},
            cookies=cookies2,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        # Now admin2 is the sole remaining admin. Attempting to delete admin2 by calling service
        # or another context must be blocked by Last Admin Protection
        with self.assertRaises(ValueError) as ctx:
            AdminService.delete_user(target_user_id=admin2["id"], current_admin_id=9999)
        self.assertIn("son yönetici", str(ctx.exception).lower())

    def test_admin_last_admin_demotion_prevented(self):
        """When only 1 admin exists, demoting their role is rejected (Last Admin Protection)."""
        admin = self._create_user(email="only_admin@istanbul.edu.tr", role="admin")
        _, cookies, csrf_token = self._login_user(admin)

        code, _, data = self._run_request(
            "POST",
            f"/admin/users/{admin['id']}/role",
            body={"role": "alumnus", "csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 400)
        self.assertIn("son yönetici", str(data).lower())

    # -------------------------------------------------------------------------
    # Job Postings Management CRUD Tests
    # -------------------------------------------------------------------------
    def test_admin_crud_jobs(self):
        """Admin can create, edit, list, and delete job postings."""
        admin = self._create_user(email="admin_jobs@istanbul.edu.tr", role="admin")
        _, cookies, csrf_token = self._login_user(admin)

        # 1. Create Job
        code, _, _ = self._run_request(
            "POST",
            "/admin/jobs",
            body={
                "title": "Machine Learning Engineer",
                "company_name": "AI Labs",
                "location": "İstanbul",
                "employment_type": "Tam Zamanlı",
                "description": "PyTorch ve NLP deneyimi",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        # Verify job in DB
        with get_db_session() as db:
            job = db.query(JobPostingDB).filter(JobPostingDB.title == "Machine Learning Engineer").first()
            self.assertIsNotNone(job)
            job_id = job.id

        # 2. Update Job
        code, _, _ = self._run_request(
            "POST",
            f"/admin/jobs/{job_id}/edit",
            body={
                "title": "Senior ML Engineer",
                "company_name": "AI Labs Global",
                "location": "Remote",
                "employment_type": "Tam Zamanlı",
                "description": "Güncellenmiş açıklama",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            updated_job = db.get(JobPostingDB, job_id)
            self.assertEqual(updated_job.title, "Senior ML Engineer")

        # 3. Delete Job
        code, _, _ = self._run_request(
            "POST",
            f"/admin/jobs/{job_id}/delete",
            body={"csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            deleted_job = db.get(JobPostingDB, job_id)
            self.assertIsNone(deleted_job)

    # -------------------------------------------------------------------------
    # Applications Review & Status Tests
    # -------------------------------------------------------------------------
    def test_admin_crud_applications(self):
        """Admin can list applications, update application status, and delete applications."""
        admin = self._create_user(email="admin_apps@istanbul.edu.tr", role="admin")
        applicant = self._create_user(email="applicant@istanbul.edu.tr", role="alumnus")
        _, cookies, csrf_token = self._login_user(admin)

        with get_db_session() as db:
            job = JobPostingDB(title="DevOps Lead", company_name="Cloud Corp")
            db.add(job)
            db.flush()
            app_record = ApplicationDB(
                user_id=applicant["id"], job_posting_id=job.id, status="pending"
            )
            db.add(app_record)
            db.flush()
            app_id = app_record.id

        # 1. List Applications
        code, _, data = self._run_request(
            "GET", "/admin/applications", cookies=cookies, headers={"accept": "application/json"}
        )
        self.assertEqual(code, 200)
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(data["applications"][0]["id"], app_id)

        # 2. Update Status to 'accepted'
        code, _, _ = self._run_request(
            "POST",
            f"/admin/applications/{app_id}/status",
            body={"status": "accepted", "csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            app_db = db.get(ApplicationDB, app_id)
            self.assertEqual(app_db.status, "accepted")

        # 3. Delete Application
        code, _, _ = self._run_request(
            "POST",
            f"/admin/applications/{app_id}/delete",
            body={"csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            app_db = db.get(ApplicationDB, app_id)
            self.assertIsNone(app_db)

    # -------------------------------------------------------------------------
    # Announcements Management CRUD Tests
    # -------------------------------------------------------------------------
    def test_admin_crud_announcements(self):
        """Admin can create, update, and delete system announcements."""
        admin = self._create_user(email="admin_ann@istanbul.edu.tr", role="admin")
        _, cookies, csrf_token = self._login_user(admin)

        # 1. Create Announcement
        code, _, _ = self._run_request(
            "POST",
            "/admin/announcements",
            body={
                "title": "2026 Mezuniyet Töreni",
                "content": "Tören Beyazıt yerleşkesinde düzenlenecektir.",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            ann = db.query(AnnouncementDB).filter(AnnouncementDB.title == "2026 Mezuniyet Töreni").first()
            self.assertIsNotNone(ann)
            ann_id = ann.id

        # 2. Update Announcement
        code, _, _ = self._run_request(
            "POST",
            f"/admin/announcements/{ann_id}/edit",
            body={
                "title": "2026 Mezuniyet Töreni (Güncellendi)",
                "content": "Tarih 15 Haziran olarak belirlendi.",
                "csrf_token": csrf_token,
            },
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            ann = db.get(AnnouncementDB, ann_id)
            self.assertEqual(ann.title, "2026 Mezuniyet Töreni (Güncellendi)")

        # 3. Delete Announcement
        code, _, _ = self._run_request(
            "POST",
            f"/admin/announcements/{ann_id}/delete",
            body={"csrf_token": csrf_token},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 303)

        with get_db_session() as db:
            ann = db.get(AnnouncementDB, ann_id)
            self.assertIsNone(ann)

    # -------------------------------------------------------------------------
    # CSRF & Security Tests
    # -------------------------------------------------------------------------
    def test_admin_csrf_protection(self):
        """State-changing admin endpoints strictly reject requests missing or with invalid CSRF token."""
        admin = self._create_user(email="admin_csrf@istanbul.edu.tr", role="admin")
        _, cookies, _ = self._login_user(admin)

        # Missing CSRF token -> 403 Forbidden
        code, _, _ = self._run_request(
            "POST",
            "/admin/jobs",
            body={"title": "Test", "company_name": "Test"},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 403, "Missing CSRF token must return 403")

        # Invalid CSRF token -> 403 Forbidden
        code, _, _ = self._run_request(
            "POST",
            "/admin/jobs",
            body={"title": "Test", "company_name": "Test", "csrf_token": "fake_invalid_token"},
            cookies=cookies,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "origin": "http://testserver",
            },
        )
        self.assertEqual(code, 403, "Invalid CSRF token must return 403")

    def test_admin_password_never_exposed(self):
        """Password hashes are never included in admin user responses or contexts."""
        admin = self._create_user(email="admin_sec@istanbul.edu.tr", role="admin")
        user = self._create_user(email="secret_hash@istanbul.edu.tr", password="SecretPassword99!")
        _, cookies, _ = self._login_user(admin)

        # Query user listing via JSON
        code, _, data = self._run_request(
            "GET", "/admin/users", cookies=cookies, headers={"accept": "application/json"}
        )
        self.assertEqual(code, 200)
        for u in data["users"]:
            self.assertNotIn("hashed_password", u, "hashed_password must never be returned in user DTO")
            self.assertNotIn("password", u)

        # Query user listing via HTML template
        code, _, html = self._run_request(
            "GET", "/admin/users", cookies=cookies, headers={"accept": "text/html"}
        )
        self.assertEqual(code, 200)
        self.assertNotIn(user["hashed_password"], html, "Password hash must not appear in HTML")


if __name__ == "__main__":
    unittest.main()
