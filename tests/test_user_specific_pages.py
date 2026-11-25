"""Comprehensive test suite for User-Specific Pages and Role-Based Experiences.

Requirements covered:
1. Alumnus role dashboard: Personal info, department, graduation year, job opportunities, applications, announcements.
2. Student role dashboard: Personal info, department, academic status, job opportunities, applications, announcements.
3. Academician role dashboard: Personal info, authored announcements, management shortcuts, university announcements.
4. Admin role dashboard: Personal info, admin banner shortcut, system statistics, admin management shortcuts.
5. Unauthenticated dashboard access: HTTP 303 Redirect to /login.
6. Role-specific application isolation:
   - Alumnus and student can view their own applications at /applications.
   - Users cannot view other users' applications.
   - Admin can view all applications.
7. Profile edit authorization guards:
   - Users cannot access or submit /users/{id}/edit for other users (HTTP 403 Forbidden).
   - Users can edit their own profile (HTTP 200 OK).
   - Admin can edit any user's profile.
8. Directory detail page action button privacy:
   - Edit and delete buttons are hidden from strangers on /users/{id}.
   - Edit and delete buttons are visible to the owner and administrators.
9. Information security:
   - Sensitive data (hashed_password, raw secrets) is never leaked in HTML or context.
"""

import asyncio
from datetime import datetime
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password
from app.main import app
from app.models.announcement import AnnouncementDB
from app.models.application import ApplicationDB
from app.models.job_posting import JobPostingDB
from app.models.user_db import UserDB
from app.services.session_service import SessionService, clear_sessions
from app.services.user_service import UserService, clear_users


class TestUserSpecificPages(unittest.TestCase):
    """Test suite verifying user-specific pages and privacy controls."""

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
        password: str = "Password123!",
        role: str = "alumnus",
        department: str = "Bilgisayar Mühendisliği",
        graduation_year: int = 2020,
    ) -> Dict[str, Any]:
        """Helper persisting a test user in PostgreSQL and UserService."""
        with get_db_session() as db:
            user = UserDB(
                name=name,
                email=email.lower().strip(),
                department=department,
                graduation_year=graduation_year,
                hashed_password=hash_password(password),
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

    def _create_job(
        self,
        title: str = "Kıdemli Yazılım Geliştirici",
        company_name: str = "Tech İÜ A.Ş.",
        location: str = "İstanbul",
        employment_type: str = "Tam Zamanlı",
        description: str = "Python ve FastAPI tecrübeli yazılım mühendisi aranıyor.",
    ) -> int:
        """Helper persisting a test job posting."""
        with get_db_session() as db:
            job = JobPostingDB(
                title=title,
                company_name=company_name,
                location=location,
                employment_type=employment_type,
                description=description,
                created_at=datetime.utcnow(),
            )
            db.add(job)
            db.flush()
            return job.id

    def _create_application(self, user_id: int, job_id: int, status: str = "pending") -> int:
        """Helper persisting a job application."""
        with get_db_session() as db:
            app_record = ApplicationDB(
                user_id=user_id,
                job_posting_id=job_id,
                status=status,
                created_at=datetime.utcnow(),
            )
            db.add(app_record)
            db.flush()
            return app_record.id

    def _create_announcement(self, title: str, content: str, created_by: Optional[int] = None) -> int:
        """Helper persisting an announcement."""
        with get_db_session() as db:
            ann = AnnouncementDB(
                title=title,
                content=content,
                created_by=created_by,
            )
            db.add(ann)
            db.flush()
            return ann.id

    @staticmethod
    def _run_request(
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], str]:
        """Dispatches an ASGI HTTP request directly to FastAPI app."""
        async def _call():
            req_headers = dict(headers or {})
            if "accept" not in req_headers:
                req_headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
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
            return response_status, response_headers, raw_text

        return asyncio.run(_call())

    # =========================================================================
    # 1. Role-Specific Dashboard Content Tests
    # =========================================================================

    def test_alumnus_dashboard_content(self):
        """Alumnus sees personal profile, department, graduation year, job opportunities, applications, and announcements."""
        alumnus = self._create_user(
            name="Ali Kaya",
            email="ali.kaya@alumni.test",
            role="alumnus",
            department="Hukuk Fakültesi",
            graduation_year=2018,
        )
        job_id = self._create_job(title="Avukat Danışman", company_name="Adalet Hukuk")
        self._create_application(user_id=alumnus["id"], job_id=job_id, status="pending")
        self._create_announcement(title="Mezunlar Günü 2026", content="Geleneksel mezun buluşması yapılacaktır.")

        _, cookies, _ = self._login_user(alumnus)

        status_code, _, html = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Personal profile details
        self.assertIn("Ali Kaya", html)
        self.assertIn("ali.kaya@alumni.test", html)
        self.assertIn("Hukuk Fakültesi", html)
        self.assertIn("2018", html)
        self.assertIn("Kayıtlı Mezun (Alumnus)", html)
        self.assertIn("Profilimi Düzenle", html)

        # Applications history
        self.assertIn("İş Başvuru Geçmişim", html)
        self.assertIn("Avukat Danışman", html)
        self.assertIn("Adalet Hukuk", html)
        self.assertIn("Değerlendiriliyor", html)

        # Job opportunities
        self.assertIn("Öne Çıkan İş Fırsatları", html)

        # Announcements
        self.assertIn("Güncel Üniversite Duyuruları", html)
        self.assertIn("Mezunlar Günü 2026", html)

        # Non-alumnus sections should NOT appear
        self.assertNotIn("Yönetim Paneline Git", html)
        self.assertNotIn("Sistem İstatistikleri", html)
        self.assertNotIn("Yayınladığım Duyurular", html)

    def test_student_dashboard_content(self):
        """Student sees personal profile, department, academic status, internship/job opportunities, applications, announcements."""
        student = self._create_user(
            name="Elif Demir",
            email="elif.demir@ogr.istanbul.edu.tr",
            role="student",
            department="Eczacılık Fakültesi",
            graduation_year=2027,
        )
        job_id = self._create_job(title="Stajyer Eczacı", company_name="Pharma İÜ")
        self._create_application(user_id=student["id"], job_id=job_id, status="accepted")
        self._create_announcement(title="Bahar Yarıyılı Sınav Takvimi", content="Sınavlar Mayıs ayında başlayacaktır.")

        _, cookies, _ = self._login_user(student)

        status_code, _, html = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Personal profile details
        self.assertIn("Elif Demir", html)
        self.assertIn("elif.demir@ogr.istanbul.edu.tr", html)
        self.assertIn("Eczacılık Fakültesi", html)
        self.assertIn("Aktif Öğrenci", html)
        self.assertIn("Kayıtlı Öğrenci", html)

        # Applications history
        self.assertIn("İş Başvuru Geçmişim", html)
        self.assertIn("Stajyer Eczacı", html)
        self.assertIn("Pharma İÜ", html)
        self.assertIn("Kabul Edildi", html)

        # Job opportunities tailored for students
        self.assertIn("Önerilen Staj ve İş İlanları", html)

        # Announcements
        self.assertIn("Bahar Yarıyılı Sınav Takvimi", html)

        # Non-student sections should NOT appear
        self.assertNotIn("Yönetim Paneline Git", html)
        self.assertNotIn("Sistem İstatistikleri", html)
        self.assertNotIn("Yayınladığım Duyurular", html)

    def test_academician_dashboard_content(self):
        """Academician sees personal profile, announcements created by the academician, management shortcuts, and university announcements."""
        acad = self._create_user(
            name="Doç. Dr. Serkan Ak",
            email="serkan.ak@istanbul.edu.tr",
            role="academician",
            department="İktisat Fakültesi",
            graduation_year=2008,
        )
        # Authored announcement by this academician
        my_ann_id = self._create_announcement(
            title="İktisat Sempozyumu Bildiri Çağrısı",
            content="Bildiri özetleri için son gün 15 Aralık.",
            created_by=acad["id"],
        )
        # Other announcement
        self._create_announcement(
            title="Kütüphane Çalışma Saatleri Güncellemesi",
            content="Merkez kütüphane 7/24 hizmet verecektir.",
            created_by=999,
        )

        _, cookies, _ = self._login_user(acad)

        status_code, _, html = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Personal profile details
        self.assertIn("Doç. Dr. Serkan Ak", html)
        self.assertIn("serkan.ak@istanbul.edu.tr", html)
        self.assertIn("İktisat Fakültesi", html)
        self.assertIn("Öğretim Görevlisi / Akademisyen", html)

        # Authored announcements
        self.assertIn("Yayınladığım Duyurular", html)
        self.assertIn("İktisat Sempozyumu Bildiri Çağrısı", html)
        self.assertIn(f'href="/announcements/{my_ann_id}/edit"', html)

        # Common announcements
        self.assertIn("Kütüphane Çalışma Saatleri Güncellemesi", html)

        # Non-academician sections should NOT appear
        self.assertNotIn("İş Başvuru Geçmişim", html)
        self.assertNotIn("Öne Çıkan İş Fırsatları", html)
        self.assertNotIn("Yönetim Paneline Git", html)

    def test_admin_dashboard_content(self):
        """Admin sees personal profile, admin dashboard banner, system statistics, and management shortcuts."""
        admin = self._create_user(
            name="Yönetici Mehmet",
            email="yonetici@istanbul.edu.tr",
            role="admin",
            department="Bilgi İşlem Daire Başkanlığı",
            graduation_year=2010,
        )
        # Add some sample database records to verify stats count
        self._create_job(title="İş 1", company_name="Şirket 1")
        self._create_announcement(title="Duyuru 1", content="İçerik 1")

        _, cookies, _ = self._login_user(admin)

        status_code, _, html = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(status_code, 200)

        # Personal profile details
        self.assertIn("Yönetici Mehmet", html)
        self.assertIn("Sistem Yöneticisi", html)

        # Admin banner and link
        self.assertIn("Yönetim Paneli", html)
        self.assertIn('href="/admin"', html)

        # System statistics
        self.assertIn("Sistem İstatistikleri", html)
        self.assertIn("Toplam Kullanıcı", html)
        self.assertIn("Kayıtlı Mezun", html)
        self.assertIn("Aktif İlanlar", html)

        # Administrative shortcuts
        self.assertIn("Kullanıcı Yönetimi", html)
        self.assertIn('href="/admin/users"', html)
        self.assertIn("İlan Yönetimi", html)
        self.assertIn('href="/admin/jobs"', html)
        self.assertIn("Başvuru İnceleme", html)
        self.assertIn('href="/admin/applications"', html)
        self.assertIn("Duyuru Yönetimi", html)
        self.assertIn('href="/admin/announcements"', html)

    def test_unauthenticated_dashboard_redirect(self):
        """Unauthenticated user accessing /dashboard is redirected to /login."""
        status_code, headers, _ = self._run_request("GET", "/dashboard")
        self.assertEqual(status_code, 303)
        self.assertIn("/login", headers.get("location", ""))

    # =========================================================================
    # 2. Application Privacy & Role-Based Isolation
    # =========================================================================

    def test_alumnus_applications_page_displays_own_applications_only(self):
        """Alumnus accessing /applications sees only their own applications, not other users' applications."""
        user_a = self._create_user(name="Kullanıcı A", email="a@test.com", role="alumnus")
        user_b = self._create_user(name="Kullanıcı B", email="b@test.com", role="alumnus")

        job_1 = self._create_job(title="Aday A Başvurduğu İlan", company_name="Firma A")
        job_2 = self._create_job(title="Aday B Gizli İlanı", company_name="Firma B")

        self._create_application(user_id=user_a["id"], job_id=job_1, status="pending")
        self._create_application(user_id=user_b["id"], job_id=job_2, status="pending")

        # User A requests /applications
        _, cookies_a, _ = self._login_user(user_a)
        st, _, html = self._run_request("GET", "/applications", cookies=cookies_a)
        self.assertEqual(st, 200)

        # User A should see their own application
        self.assertIn("Aday A Başvurduğu İlan", html)
        self.assertIn("Firma A", html)
        self.assertIn("Kullanıcı A", html)

        # User A must NOT see User B's application or name
        self.assertNotIn("Aday B Gizli İlanı", html)
        self.assertNotIn("Firma B", html)
        self.assertNotIn("Kullanıcı B", html)

    def test_admin_applications_page_displays_all_applications(self):
        """Admin accessing /applications sees applications from all users."""
        user_a = self._create_user(name="Aday A", email="aday.a@test.com", role="alumnus")
        user_b = self._create_user(name="Aday B", email="aday.b@test.com", role="student")
        admin = self._create_user(name="Yönetici", email="admin@test.com", role="admin")

        job = self._create_job(title="Genel Başvuru İlanı", company_name="Holding")
        self._create_application(user_id=user_a["id"], job_id=job, status="accepted")
        self._create_application(user_id=user_b["id"], job_id=job, status="pending")

        _, admin_cookies, _ = self._login_user(admin)
        st, _, html = self._run_request("GET", "/applications", cookies=admin_cookies)
        self.assertEqual(st, 200)

        # Admin sees both
        self.assertIn("Aday A", html)
        self.assertIn("Aday B", html)

    # =========================================================================
    # 3. Privacy & Profile Authorization Guards
    # =========================================================================

    def test_user_cannot_edit_another_users_profile(self):
        """Non-admin user cannot edit another user's profile (HTTP 403 Forbidden)."""
        user_a = self._create_user(name="User A", email="usera@test.com", role="alumnus")
        user_b = self._create_user(name="User B", email="userb@test.com", role="alumnus")

        _, cookies_a, csrf_a = self._login_user(user_a)

        # User A tries to GET User B's edit form
        get_st, _, get_html = self._run_request("GET", f"/users/{user_b['id']}/edit", cookies=cookies_a)
        self.assertEqual(get_st, 403)
        self.assertIn("yetkiniz bulunmamaktadır", get_html)

        # User A tries to POST update to User B's profile
        post_st, _, post_html = self._run_request(
            "POST",
            f"/users/{user_b['id']}/edit",
            body={
                "name": "Hacked Name",
                "email": "hacked@test.com",
                "department": "Hacked",
                "graduation_year": 2025,
                "csrf_token": csrf_a,
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
            cookies=cookies_a,
        )
        self.assertEqual(post_st, 403)

    def test_user_can_edit_own_profile(self):
        """User can access and update their own profile."""
        user = self._create_user(name="Asıl Kullanıcı", email="asil@test.com", role="alumnus")
        _, cookies, csrf = self._login_user(user)

        # GET own edit form
        get_st, _, html = self._run_request("GET", f"/users/{user['id']}/edit", cookies=cookies)
        self.assertEqual(get_st, 200)
        self.assertIn("Asıl Kullanıcı", html)

        # POST update to own profile
        post_st, _, post_html = self._run_request(
            "POST",
            f"/users/{user['id']}/edit",
            body={
                "name": "Güncel İsim",
                "email": "asil@test.com",
                "department": "Bilgisayar Mühendisliği",
                "graduation_year": 2021,
                "csrf_token": csrf,
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
            cookies=cookies,
        )
        self.assertEqual(post_st, 200)
        self.assertIn("Güncel İsim", post_html)

    def test_user_detail_page_hides_action_buttons_from_strangers(self):
        """Viewing another user's profile hides edit and delete buttons from non-owners and non-admins."""
        target_user = self._create_user(name="Hedef Kullanıcı", email="hedef@test.com", role="alumnus")
        viewer_user = self._create_user(name="İzleyici Kullanıcı", email="izleyici@test.com", role="alumnus")
        admin_user = self._create_user(name="Yönetici", email="admin.det@test.com", role="admin")

        # 1. Unauthenticated stranger views target user
        st, _, html_guest = self._run_request("GET", f"/users/{target_user['id']}")
        self.assertEqual(st, 200)
        self.assertIn("Hedef Kullanıcı", html_guest)
        self.assertNotIn(f'href="/users/{target_user["id"]}/edit"', html_guest)
        self.assertNotIn(f'action="/users/{target_user["id"]}/delete"', html_guest)

        # 2. Authenticated non-owner stranger views target user
        _, cookies_viewer, _ = self._login_user(viewer_user)
        st, _, html_viewer = self._run_request("GET", f"/users/{target_user['id']}", cookies=cookies_viewer)
        self.assertEqual(st, 200)
        self.assertIn("Hedef Kullanıcı", html_viewer)
        self.assertNotIn(f'href="/users/{target_user["id"]}/edit"', html_viewer)
        self.assertNotIn(f'action="/users/{target_user["id"]}/delete"', html_viewer)

        # 3. Owner views their own profile
        _, cookies_owner, _ = self._login_user(target_user)
        st, _, html_owner = self._run_request("GET", f"/users/{target_user['id']}", cookies=cookies_owner)
        self.assertEqual(st, 200)
        self.assertIn(f'href="/users/{target_user["id"]}/edit"', html_owner)
        self.assertIn(f'action="/users/{target_user["id"]}/delete"', html_owner)

        # 4. Admin views target user's profile
        _, cookies_admin, _ = self._login_user(admin_user)
        st, _, html_admin = self._run_request("GET", f"/users/{target_user['id']}", cookies=cookies_admin)
        self.assertEqual(st, 200)
        self.assertIn(f'href="/users/{target_user["id"]}/edit"', html_admin)
        self.assertIn(f'action="/users/{target_user["id"]}/delete"', html_admin)

    def test_sensitive_data_not_exposed_on_dashboard(self):
        """Password hashes, raw password fields, and server secrets must never be exposed on dashboard."""
        user = self._create_user(
            name="Gizli Kullanıcı",
            email="gizli@test.com",
            password="UltraSecretPassword123!",
            role="alumnus",
        )
        _, cookies, _ = self._login_user(user)

        st, _, html = self._run_request("GET", "/dashboard", cookies=cookies)
        self.assertEqual(st, 200)

        # Must not contain plaintext password
        self.assertNotIn("UltraSecretPassword123!", html)
        # Must not contain hashed password string or key
        self.assertNotIn("hashed_password", html)
        self.assertNotIn(user["hashed_password"], html)
        # Must not contain server-side secret key
        self.assertNotIn(settings.SECRET_KEY, html)


if __name__ == "__main__":
    unittest.main()
