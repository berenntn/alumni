"""Unit and integration tests for Alumni User Registration."""

import json
import unittest
from typing import Any, Dict, Optional, Tuple
import urllib.parse

from app.core.database import get_db_session
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.user_db import UserDB
from app.services.registration_service import RegistrationService, register_user
from app.services.user_service import UserService, clear_users


class TestRegistration(unittest.TestCase):
    """Test suite verifying validation, security, and persistence for User Registration."""

    def setUp(self):
        """Clean database and in-memory stores before each test."""
        clear_users()
        with get_db_session() as db:
            db.query(UserDB).delete()

    def tearDown(self):
        """Clean database and in-memory stores after each test."""
        clear_users()
        with get_db_session() as db:
            db.query(UserDB).delete()

    @staticmethod
    def _run_request(
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], Any]:
        """Dispatches an ASGI HTTP request directly to the FastAPI app without external dependencies."""
        async def _asgi_call():
            req_headers = dict(headers or {})
            body_bytes = b""

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
                        response_headers[k.decode("latin-1")] = v.decode("latin-1")
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

    def test_get_register_page(self):
        """GET /register should return HTTP 200 with all required form fields."""
        status_code, headers, body = self._run_request("GET", "/register")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn('name="name"', body)
        self.assertIn('name="email"', body)
        self.assertIn('name="department"', body)
        self.assertIn('name="graduation_year"', body)
        self.assertIn('name="password"', body)
        self.assertIn('name="confirm_password"', body)
        self.assertIn("Aramıza Katılın", body)

    def test_get_login_page(self):
        """GET /login should return HTTP 200 explaining Phase 3 roadmap status."""
        status_code, headers, body = self._run_request("GET", "/login")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Aşama 3", body)
        self.assertIn("/register", body)

    def test_successful_registration_html(self):
        """Submitting valid HTML form should return HTTP 200 with success message and DB persistence."""
        form_payload = {
            "name": "Prof. Dr. Aziz Sancar",
            "email": "aziz.sancar@alumni.istanbul.edu.tr",
            "department": "Tıp Fakültesi",
            "graduation_year": "1969",
            "password": "NobelPassword2015!",
            "confirm_password": "NobelPassword2015!",
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status_code, _, body = self._run_request("POST", "/register", body=form_payload, headers=headers)

        self.assertEqual(status_code, 200)
        self.assertIn("Kaydınız Başarıyla Tamamlandı!", body)
        self.assertIn("Prof. Dr. Aziz Sancar", body)
        self.assertIn("aziz.sancar@alumni.istanbul.edu.tr", body)
        self.assertIn("/login", body)
        # Ensure password is never leaked in HTML output
        self.assertNotIn("NobelPassword2015!", body)

        # Verify DB persistence
        with get_db_session() as db:
            user = db.query(UserDB).filter(UserDB.email == "aziz.sancar@alumni.istanbul.edu.tr").first()
            self.assertIsNotNone(user)
            user_id = user.id
            self.assertEqual(user.name, "Prof. Dr. Aziz Sancar")
            self.assertEqual(user.department, "Tıp Fakültesi")
            self.assertEqual(user.graduation_year, 1969)
            self.assertEqual(user.role, "alumnus")
            self.assertTrue(verify_password("NobelPassword2015!", user.hashed_password))

        # Verify in-memory synchronization
        mem_user = UserService.get_user(user_id)
        self.assertIsNotNone(mem_user)
        self.assertEqual(mem_user.email, "aziz.sancar@alumni.istanbul.edu.tr")

    def test_successful_registration_json_api(self):
        """Submitting JSON payload to POST /register with Accept: application/json returns HTTP 201."""
        json_payload = {
            "name": "Ayşe Yılmaz",
            "email": "ayse.yilmaz@alumni.istanbul.edu.tr",
            "department": "Hukuk",
            "graduation_year": 2022,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
        }
        status_code, _, data = self._run_request("POST", "/register", body=json_payload, headers=headers)

        self.assertEqual(status_code, 201)
        self.assertEqual(data.get("status"), "success")
        user_data = data.get("data", {})
        self.assertEqual(user_data.get("name"), "Ayşe Yılmaz")
        self.assertEqual(user_data.get("email"), "ayse.yilmaz@alumni.istanbul.edu.tr")
        self.assertEqual(user_data.get("role"), "alumnus")
        self.assertNotIn("password", user_data)
        self.assertNotIn("hashed_password", user_data)

    def test_invalid_email_format(self):
        """Registration with an invalid email address should be rejected with HTTP 400."""
        invalid_emails = ["notanemail", "user@", "@domain.com", "user@domain"]
        for bad_email in invalid_emails:
            payload = {
                "name": "Test User",
                "email": bad_email,
                "department": "İktisat",
                "graduation_year": 2020,
                "password": "ValidPassword123",
                "confirm_password": "ValidPassword123",
            }
            status_code, _, data = self._run_request(
                "POST",
                "/register",
                body=payload,
                headers={"content-type": "application/json", "accept": "application/json"},
            )
            self.assertEqual(status_code, 400, f"Expected 400 for email: {bad_email}")
            self.assertEqual(data.get("status"), "error")
            self.assertIn("e-posta", data.get("message", "").lower())

        # Ensure no records in DB
        with get_db_session() as db:
            self.assertEqual(db.query(UserDB).count(), 0)

    def test_missing_required_fields(self):
        """Missing any required field must be rejected with HTTP 400."""
        base_payload = {
            "name": "Mehmet Demir",
            "email": "mehmet@alumni.istanbul.edu.tr",
            "department": "Felsefe",
            "graduation_year": 2021,
            "password": "Password123!",
            "confirm_password": "Password123!",
        }

        for field in ["name", "email", "department", "graduation_year", "password", "confirm_password"]:
            payload = dict(base_payload)
            del payload[field]
            status_code, _, data = self._run_request(
                "POST",
                "/register",
                body=payload,
                headers={"content-type": "application/json", "accept": "application/json"},
            )
            self.assertEqual(status_code, 400, f"Expected 400 when missing {field}")
            self.assertEqual(data.get("status"), "error")

        with get_db_session() as db:
            self.assertEqual(db.query(UserDB).count(), 0)

    def test_password_mismatch(self):
        """Password mismatch between password and confirm_password must return HTTP 400."""
        payload = {
            "name": "Canan Dağ",
            "email": "canan@alumni.istanbul.edu.tr",
            "department": "Eczacılık",
            "graduation_year": 2023,
            "password": "Password123!",
            "confirm_password": "DifferentPassword456!",
        }
        status_code, _, data = self._run_request(
            "POST",
            "/register",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("eşleşmiyor", data.get("message", ""))

        with get_db_session() as db:
            self.assertEqual(db.query(UserDB).count(), 0)

    def test_password_shorter_than_8_characters(self):
        """Passwords shorter than 8 characters must return HTTP 400."""
        payload = {
            "name": "Kerem Barış",
            "email": "kerem@alumni.istanbul.edu.tr",
            "department": "Sosyoloji",
            "graduation_year": 2024,
            "password": "short",
            "confirm_password": "short",
        }
        status_code, _, data = self._run_request(
            "POST",
            "/register",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("8 karakter", data.get("message", ""))

        with get_db_session() as db:
            self.assertEqual(db.query(UserDB).count(), 0)

    def test_duplicate_email_prevention(self):
        """Registering with an already existing email (case-insensitive) must return HTTP 400."""
        initial_payload = {
            "name": "Ali Veli",
            "email": "ali.veli@alumni.istanbul.edu.tr",
            "department": "Fizik",
            "graduation_year": 2020,
            "password": "FirstPassword123!",
            "confirm_password": "FirstPassword123!",
        }
        # First registration succeeds
        status_code_1, _, data_1 = self._run_request(
            "POST",
            "/register",
            body=initial_payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code_1, 201)

        # Second registration with identical email (uppercase variation) must fail
        duplicate_payload = {
            "name": "Ali Veli Clone",
            "email": "ALI.VELI@ALUMNI.ISTANBUL.EDU.TR",
            "department": "Matematik",
            "graduation_year": 2021,
            "password": "SecondPassword456!",
            "confirm_password": "SecondPassword456!",
        }
        status_code_2, _, data_2 = self._run_request(
            "POST",
            "/register",
            body=duplicate_payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code_2, 400)
        self.assertEqual(data_2.get("status"), "error")
        self.assertIn("zaten mevcut", data_2.get("message", ""))

        # Only 1 user should exist in DB
        with get_db_session() as db:
            self.assertEqual(db.query(UserDB).count(), 1)

    def test_password_hashing_security(self):
        """Password stored in PostgreSQL must be a secure hash and never plaintext."""
        registered = register_user(
            name="Zeynep Kaya",
            email="zeynep@alumni.istanbul.edu.tr",
            department="Kimya",
            graduation_year=2022,
            password="MySecretPassword99!",
            confirm_password="MySecretPassword99!",
        )
        self.assertIsNotNone(registered.get("id"))

        with get_db_session() as db:
            db_user = db.query(UserDB).filter(UserDB.id == registered["id"]).first()
            self.assertIsNotNone(db_user)
            self.assertNotEqual(db_user.hashed_password, "MySecretPassword99!")
            self.assertTrue(db_user.hashed_password.startswith("pbkdf2_sha256$100000$"))
            self.assertTrue(verify_password("MySecretPassword99!", db_user.hashed_password))
            self.assertFalse(verify_password("WrongPassword123!", db_user.hashed_password))

    def test_prevent_role_privilege_escalation(self):
        """Clients cannot assign themselves administrator or other elevated roles."""
        payload = {
            "name": "Hacker Alumnus",
            "email": "hacker@alumni.istanbul.edu.tr",
            "department": "Siber Güvenlik",
            "graduation_year": 2023,
            "password": "HackerPassword123!",
            "confirm_password": "HackerPassword123!",
            "role": "admin",
            "is_admin": True,
        }
        status_code, _, data = self._run_request(
            "POST",
            "/register",
            body=payload,
            headers={"content-type": "application/json", "accept": "application/json"},
        )
        self.assertEqual(status_code, 201)
        self.assertEqual(data["data"]["role"], "alumnus")

        with get_db_session() as db:
            user = db.query(UserDB).filter(UserDB.email == "hacker@alumni.istanbul.edu.tr").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "alumnus")


if __name__ == "__main__":
    unittest.main()
