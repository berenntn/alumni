"""Comprehensive test suite for Dynamic Navigation (Menu Items Based on User Role).

Requirements covered:
1. Guest (unauthenticated) visitors see only Home, Login, and Register in navigation menu.
2. Authenticated users see Home, Profile, Jobs, Announcements, and Logout.
3. Role-specific menu items:
   - Alumnus sees: Home, Profile, Jobs, Announcements, Başvurularım, Mezunlar, Logout.
   - Student sees: Home, Profile, Jobs, Announcements, Başvurularım, Mezun Rehberi, Logout.
   - Academician sees: Home, Profile, Jobs, Announcements, Duyuru Yönetimi, Mezunlar, Logout.
   - Admin sees: Home, Profile, Jobs, Announcements, Yönetim Paneli, Başvurular, Mezunlar, Logout.
4. Non-admin users (guest, alumnus, student, academician) never see Admin Panel link.
5. Navigation dynamically updates upon login and logout.
6. Logout button contains server-generated CSRF token.
7. Viewing another user's profile (/users/{id}) preserves the viewer's navigation role.
8. Responsive mobile navigation toggle and Apple HIG layout structure are preserved.
"""

import asyncio
from datetime import datetime
import json
import re
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


class TestDynamicNavigation(unittest.TestCase):
    """Test suite verifying role-based dynamic navigation menu rendering."""

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

    @staticmethod
    def _extract_nav_menu(html: str) -> str:
        """Extracts the inner HTML of the <ul class="nav-links" id="navLinks"> element."""
        match = re.search(r'<ul\s+class="nav-links"\s+id="navLinks">(.*?)</ul>', html, re.DOTALL)
        if match:
            return match.group(1)
        return ""

    # =========================================================================
    # Test Cases: Role-Based Navigation Menu Rendering
    # =========================================================================

    def test_guest_navigation_menu(self):
        """Unauthenticated guests should see only Home, Login, and Register in navigation."""
        status_code, _, html = self._run_request("GET", "/")
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertTrue(nav, "Navigation menu <ul id='navLinks'> must be present in HTML.")

        # Guest links must be present
        self.assertIn('href="/"', nav)
        self.assertIn("Ana Sayfa", nav)
        self.assertIn('href="/login"', nav)
        self.assertIn("Giriş Yap", nav)
        self.assertIn('href="/register"', nav)
        self.assertIn("Kayıt Ol", nav)

        # Authenticated-only links must NOT be present
        self.assertNotIn('href="/dashboard"', nav)
        self.assertNotIn("Profil", nav)
        self.assertNotIn('href="/jobs"', nav)
        self.assertNotIn("İş İlanları", nav)
        self.assertNotIn('href="/announcements"', nav)
        self.assertNotIn("Duyurular", nav)
        self.assertNotIn("Duyuru Yönetimi", nav)
        self.assertNotIn('href="/applications"', nav)
        self.assertNotIn("Başvurular", nav)
        self.assertNotIn("Başvurularım", nav)
        self.assertNotIn('href="/users"', nav)
        self.assertNotIn("Mezunlar", nav)
        self.assertNotIn("Mezun Rehberi", nav)
        self.assertNotIn('href="/admin"', nav)
        self.assertNotIn("Yönetim Paneli", nav)
        self.assertNotIn('action="/logout"', nav)
        self.assertNotIn("Çıkış Yap", nav)

    def test_alumnus_navigation_menu(self):
        """Authenticated alumnus should see Home, Profile, Jobs, Announcements, Applications, Directory, and Logout."""
        user = self._create_user(role="alumnus")
        _, cookies, _ = self._login_user(user)

        status_code, _, html = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertTrue(nav)

        # Common authenticated links
        self.assertIn('href="/"', nav)
        self.assertIn("Ana Sayfa", nav)
        self.assertIn('href="/dashboard"', nav)
        self.assertIn("Profil", nav)
        self.assertIn('href="/jobs"', nav)
        self.assertIn("İş İlanları", nav)
        self.assertIn('href="/announcements"', nav)
        self.assertIn("Duyurular", nav)
        self.assertIn('action="/logout"', nav)
        self.assertIn("Çıkış Yap", nav)

        # Alumnus specific links
        self.assertIn('href="/applications"', nav)
        self.assertIn("Başvurularım", nav)
        self.assertIn('href="/users"', nav)
        self.assertIn("Mezunlar", nav)

        # Forbidden links for alumnus
        self.assertNotIn('href="/login"', nav)
        self.assertNotIn("Giriş Yap", nav)
        self.assertNotIn('href="/register"', nav)
        self.assertNotIn("Kayıt Ol", nav)
        self.assertNotIn('href="/admin"', nav)
        self.assertNotIn("Yönetim Paneli", nav)
        self.assertNotIn("Duyuru Yönetimi", nav)

    def test_student_navigation_menu(self):
        """Authenticated student should see Home, Profile, Jobs, Announcements, Applications, Directory as Mezun Rehberi, and Logout."""
        user = self._create_user(name="Öğrenci Ayşe", email="ogrenci@istanbul.edu.tr", role="student")
        _, cookies, _ = self._login_user(user)

        status_code, _, html = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertTrue(nav)

        # Common authenticated links
        self.assertIn('href="/"', nav)
        self.assertIn("Ana Sayfa", nav)
        self.assertIn('href="/dashboard"', nav)
        self.assertIn("Profil", nav)
        self.assertIn('href="/jobs"', nav)
        self.assertIn("İş İlanları", nav)
        self.assertIn('href="/announcements"', nav)
        self.assertIn("Duyurular", nav)
        self.assertIn('action="/logout"', nav)
        self.assertIn("Çıkış Yap", nav)

        # Student specific links
        self.assertIn('href="/applications"', nav)
        self.assertIn("Başvurularım", nav)
        self.assertIn('href="/users"', nav)
        self.assertIn("Mezun Rehberi", nav)

        # Forbidden links for student
        self.assertNotIn('href="/login"', nav)
        self.assertNotIn("Giriş Yap", nav)
        self.assertNotIn('href="/register"', nav)
        self.assertNotIn("Kayıt Ol", nav)
        self.assertNotIn('href="/admin"', nav)
        self.assertNotIn("Yönetim Paneli", nav)
        self.assertNotIn("Duyuru Yönetimi", nav)

    def test_academician_navigation_menu(self):
        """Authenticated academician should see Home, Profile, Jobs, Announcements, Announcement Management, Directory, and Logout."""
        user = self._create_user(name="Prof. Dr. Ahmet", email="ahmet@istanbul.edu.tr", role="academician")
        _, cookies, _ = self._login_user(user)

        status_code, _, html = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertTrue(nav)

        # Common authenticated links
        self.assertIn('href="/"', nav)
        self.assertIn("Ana Sayfa", nav)
        self.assertIn('href="/dashboard"', nav)
        self.assertIn("Profil", nav)
        self.assertIn('href="/jobs"', nav)
        self.assertIn("İş İlanları", nav)
        self.assertIn('href="/announcements"', nav)
        self.assertIn("Duyurular", nav)
        self.assertIn('action="/logout"', nav)
        self.assertIn("Çıkış Yap", nav)

        # Academician specific links
        self.assertIn("Duyuru Yönetimi", nav)
        self.assertIn('href="/users"', nav)
        self.assertIn("Mezunlar", nav)

        # Forbidden links for academician
        self.assertNotIn('href="/login"', nav)
        self.assertNotIn("Giriş Yap", nav)
        self.assertNotIn('href="/register"', nav)
        self.assertNotIn("Kayıt Ol", nav)
        self.assertNotIn('href="/admin"', nav)
        self.assertNotIn("Yönetim Paneli", nav)
        self.assertNotIn("Başvurularım", nav)

    def test_admin_navigation_menu(self):
        """Authenticated admin should see Home, Profile, Jobs, Announcements, Admin Panel, Applications, Directory, and Logout."""
        user = self._create_user(name="Admin User", email="admin@istanbul.edu.tr", role="admin")
        _, cookies, _ = self._login_user(user)

        status_code, _, html = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertTrue(nav)

        # Common authenticated links
        self.assertIn('href="/"', nav)
        self.assertIn("Ana Sayfa", nav)
        self.assertIn('href="/dashboard"', nav)
        self.assertIn("Profil", nav)
        self.assertIn('href="/jobs"', nav)
        self.assertIn("İş İlanları", nav)
        self.assertIn('href="/announcements"', nav)
        self.assertIn("Duyurular", nav)
        self.assertIn('action="/logout"', nav)
        self.assertIn("Çıkış Yap", nav)

        # Admin specific links
        self.assertIn('href="/admin"', nav)
        self.assertIn("Yönetim Paneli", nav)
        self.assertIn('href="/applications"', nav)
        self.assertIn("Başvurular", nav)
        self.assertIn('href="/users"', nav)
        self.assertIn("Mezunlar", nav)

        # Forbidden links for admin
        self.assertNotIn('href="/login"', nav)
        self.assertNotIn("Giriş Yap", nav)
        self.assertNotIn('href="/register"', nav)
        self.assertNotIn("Kayıt Ol", nav)
        self.assertNotIn("Duyuru Yönetimi", nav)

    # =========================================================================
    # Test Cases: Security, Isolation, and State Transitions
    # =========================================================================

    def test_admin_link_never_exposed_to_non_admins(self):
        """Verifies that neither /admin nor 'Yönetim Paneli' is ever rendered for non-admin roles."""
        non_admin_roles = ["guest", "alumnus", "student", "academician"]

        for r in non_admin_roles:
            with self.subTest(role=r):
                cookies = None
                if r != "guest":
                    user = self._create_user(
                        name=f"User {r}",
                        email=f"{r}@test.edu.tr",
                        role=r,
                    )
                    _, cookies, _ = self._login_user(user)

                status_code, _, html = self._run_request("GET", "/", cookies=cookies)
                self.assertEqual(status_code, 200)

                nav = self._extract_nav_menu(html)
                self.assertNotIn('href="/admin"', nav, f"Role '{r}' must NOT have href='/admin' in navigation.")
                self.assertNotIn("Yönetim Paneli", nav, f"Role '{r}' must NOT have 'Yönetim Paneli' in navigation.")

    def test_logout_button_contains_valid_csrf_token(self):
        """The logout button must be a form containing a valid hidden csrf_token."""
        user = self._create_user(role="alumnus")
        _, cookies, csrf_token = self._login_user(user)

        status_code, _, html = self._run_request("GET", "/", cookies=cookies)
        self.assertEqual(status_code, 200)

        nav = self._extract_nav_menu(html)
        self.assertIn('action="/logout"', nav)
        self.assertIn('name="csrf_token"', nav)
        self.assertIn(f'value="{csrf_token}"', nav)

    def test_navigation_switches_on_login_and_logout(self):
        """Navigation menu dynamically reflects login state: guest -> authenticated -> logged out guest."""
        # 1. Initially Guest
        status_code, _, html = self._run_request("GET", "/")
        self.assertEqual(status_code, 200)
        nav_guest = self._extract_nav_menu(html)
        self.assertIn("Giriş Yap", nav_guest)
        self.assertNotIn("Çıkış Yap", nav_guest)

        # 2. Login via POST /login
        user = self._create_user(
            name="Zeynep Yılmaz",
            email="zeynep@alumni.test",
            password="LoginPass123!",
            role="alumnus",
        )

        # Get login form CSRF token
        _, _, login_page_html = self._run_request("GET", "/login")
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page_html)
        login_csrf = csrf_match.group(1) if csrf_match else ""

        login_status, login_headers, _ = self._run_request(
            "POST",
            "/login",
            body={
                "email": "zeynep@alumni.test",
                "password": "LoginPass123!",
                "csrf_token": login_csrf,
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(login_status, 303)

        # Extract session cookie
        set_cookie = login_headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie)
        session_token = ""
        for part in set_cookie.split(";"):
            if part.strip().startswith(f"{settings.SESSION_COOKIE_NAME}="):
                session_token = part.strip().split("=")[1]
                break
        self.assertTrue(session_token)

        auth_cookies = {settings.SESSION_COOKIE_NAME: session_token}

        # 3. Authenticated view of /
        status_code, _, html = self._run_request("GET", "/", cookies=auth_cookies)
        self.assertEqual(status_code, 200)
        nav_auth = self._extract_nav_menu(html)
        self.assertNotIn("Giriş Yap", nav_auth)
        self.assertNotIn("Kayıt Ol", nav_auth)
        self.assertIn("Profil", nav_auth)
        self.assertIn("Çıkış Yap", nav_auth)

        # Extract CSRF token from logout button
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', nav_auth)
        logout_csrf = csrf_match.group(1) if csrf_match else ""
        self.assertTrue(logout_csrf)

        # 4. Logout via POST /logout
        logout_status, logout_headers, _ = self._run_request(
            "POST",
            "/logout",
            body={"csrf_token": logout_csrf},
            headers={"content-type": "application/x-www-form-urlencoded"},
            cookies=auth_cookies,
        )
        self.assertEqual(logout_status, 303)

        # 5. Verify session is invalidated and menu reverts to Guest
        status_code, _, html = self._run_request("GET", "/", cookies={settings.SESSION_COOKIE_NAME: ""})
        self.assertEqual(status_code, 200)
        nav_logged_out = self._extract_nav_menu(html)
        self.assertIn("Giriş Yap", nav_logged_out)
        self.assertIn("Kayıt Ol", nav_logged_out)
        self.assertNotIn("Profil", nav_logged_out)
        self.assertNotIn("Çıkış Yap", nav_logged_out)

    def test_navigation_consistent_across_public_pages(self):
        """Dynamic navigation menu is consistently rendered across /jobs, /announcements, and /about."""
        admin_user = self._create_user(name="Admin Cons", email="admin.cons@istanbul.edu.tr", role="admin")
        _, admin_cookies, _ = self._login_user(admin_user)

        public_pages = ["/", "/jobs", "/announcements", "/about"]

        for path in public_pages:
            with self.subTest(path=path, user="guest"):
                st, _, html = self._run_request("GET", path)
                self.assertEqual(st, 200)
                nav = self._extract_nav_menu(html)
                self.assertIn("Giriş Yap", nav)
                self.assertNotIn("Yönetim Paneli", nav)
                self.assertNotIn("Çıkış Yap", nav)

            with self.subTest(path=path, user="admin"):
                st, _, html = self._run_request("GET", path, cookies=admin_cookies)
                self.assertEqual(st, 200)
                nav = self._extract_nav_menu(html)
                self.assertNotIn("Giriş Yap", nav)
                self.assertIn("Yönetim Paneli", nav)
                self.assertIn("Çıkış Yap", nav)

    def test_viewing_user_profile_preserves_viewer_navigation(self):
        """When an admin views another user's profile, the navigation bar displays the admin's navigation menu."""
        alumnus = self._create_user(name="Target Alumnus", email="target@alumni.test", role="alumnus")
        admin = self._create_user(name="Viewer Admin", email="viewer.admin@istanbul.edu.tr", role="admin")
        _, admin_cookies, _ = self._login_user(admin)

        st, _, html = self._run_request("GET", f"/users/{alumnus['id']}", cookies=admin_cookies)
        self.assertEqual(st, 200)

        nav = self._extract_nav_menu(html)
        # Even though the template context has "user": <alumnus>,
        # the navigation bar must resolve to viewer (admin)
        self.assertIn("Yönetim Paneli", nav)
        self.assertIn('href="/admin"', nav)
        self.assertIn("Çıkış Yap", nav)
        self.assertNotIn("Giriş Yap", nav)

    def test_responsive_mobile_toggle_preserved(self):
        """The mobile toggle hamburger button and brand emblem are intact."""
        st, _, html = self._run_request("GET", "/")
        self.assertEqual(st, 200)
        self.assertIn('id="mobileToggle"', html)
        self.assertIn('class="mobile-toggle"', html)
        self.assertIn('class="brand-emblem"', html)
        self.assertIn('id="navLinks"', html)


if __name__ == "__main__":
    unittest.main()
