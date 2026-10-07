"""Unit and integration tests for User, ApiUser, Web View CRUD, and Health routes via ASGI."""

import asyncio
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.controllers.user_controller import UserController
from app.main import app
from app.services.user_service import clear_users


class TestRoutes(unittest.TestCase):
    """Test suite verifying route-to-controller integration, View layer CRUD, and HTTP endpoints."""

    def setUp(self):
        """Reset the in-memory user store before each test."""
        clear_users()

    def tearDown(self):
        """Clean up in-memory user store after each test."""
        clear_users()

    @staticmethod
    def _run_request(
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], Any]:
        """Dispatches an ASGI HTTP request directly to FastAPI app without httpx."""

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
                    # Default to application/json if not specified
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

            raw_body = b"".join(response_chunks)
            parsed_data: Any = raw_body.decode("utf-8", errors="replace")
            resp_content_type = response_headers.get("content-type", "")
            if "application/json" in resp_content_type:
                try:
                    parsed_data = json.loads(parsed_data)
                except Exception:
                    pass

            return status_code[0], response_headers, parsed_data

        return asyncio.run(_asgi_call())

    # -------------------------------------------------------------------------
    # REST API User Routes (app/api/user_routes.py -> ApiUserController)
    # -------------------------------------------------------------------------

    def test_api_get_users_empty(self):
        """GET /api/users should return 200 with empty user list."""
        status_code, _, data = self._run_request("GET", "/api/users")
        self.assertEqual(status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["data"], [])

    def test_api_create_user(self):
        """POST /api/users should return 201 Created and user details."""
        payload = {
            "name": "Berkay Tuna",
            "email": "berkay@example.com",
            "department": "Bilgisayar Mühendisliği",
            "graduation_year": 2024,
        }
        status_code, _, data = self._run_request("POST", "/api/users", body=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["status"], "success")
        self.assertIn("User created successfully", data["message"])
        self.assertIsNotNone(data["data"])
        self.assertEqual(data["data"]["id"], 1)
        self.assertEqual(data["data"]["name"], "Berkay Tuna")
        self.assertEqual(data["data"]["email"], "berkay@example.com")
        self.assertEqual(data["data"]["department"], "Bilgisayar Mühendisliği")
        self.assertEqual(data["data"]["graduation_year"], 2024)

    def test_api_get_user_by_id(self):
        """GET /api/users/{id} should return 200 for existing user and 404 for missing."""
        payload = {
            "name": "Ayşe Yılmaz",
            "email": "ayse@example.com",
            "department": "Hukuk",
            "graduation_year": 2022,
        }
        create_status, _, create_data = self._run_request(
            "POST", "/api/users", body=payload
        )
        self.assertEqual(create_status, 201)
        user_id = create_data["data"]["id"]

        get_status, _, get_data = self._run_request("GET", f"/api/users/{user_id}")
        self.assertEqual(get_status, 200)
        self.assertEqual(get_data["status"], "success")
        self.assertEqual(get_data["data"]["name"], "Ayşe Yılmaz")

        missing_status, _, missing_data = self._run_request(
            "GET", "/api/users/999"
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")
        self.assertIn("not found", missing_data["message"])

    def test_api_update_user_put(self):
        """PUT /api/users/{id} should return 200 on full update and 404 when missing."""
        payload = {
            "name": "Mehmet Demir",
            "email": "mehmet@old.com",
            "department": "İktisat",
            "graduation_year": 2020,
        }
        _, _, create_data = self._run_request("POST", "/api/users", body=payload)
        user_id = create_data["data"]["id"]

        update_payload = {
            "name": "Mehmet Demir",
            "email": "mehmet@new.com",
            "department": "Maliye",
            "graduation_year": 2021,
        }
        put_status, _, put_data = self._run_request(
            "PUT", f"/api/users/{user_id}", body=update_payload
        )
        self.assertEqual(put_status, 200)
        self.assertEqual(put_data["status"], "success")
        self.assertEqual(put_data["data"]["email"], "mehmet@new.com")
        self.assertEqual(put_data["data"]["department"], "Maliye")
        self.assertEqual(put_data["data"]["graduation_year"], 2021)

        missing_status, _, missing_data = self._run_request(
            "PUT", "/api/users/999", body=update_payload
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")

    def test_api_patch_user(self):
        """PATCH /api/users/{id} should return 200 on partial update and 404 when missing."""
        payload = {
            "name": "Selin Kaya",
            "email": "selin@old.com",
            "department": "Mimarlık",
            "graduation_year": 2019,
        }
        _, _, create_data = self._run_request("POST", "/api/users", body=payload)
        user_id = create_data["data"]["id"]

        patch_status, _, patch_data = self._run_request(
            "PATCH", f"/api/users/{user_id}", body={"email": "selin@new.com"}
        )
        self.assertEqual(patch_status, 200)
        self.assertEqual(patch_data["status"], "success")
        self.assertEqual(patch_data["data"]["email"], "selin@new.com")
        self.assertEqual(patch_data["data"]["name"], "Selin Kaya")

        missing_status, _, missing_data = self._run_request(
            "PATCH", "/api/users/999", body={"email": "ghost@ghost.com"}
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")

    def test_api_delete_user(self):
        """DELETE /api/users/{id} should return 200 on deletion and 404 when missing."""
        payload = {
            "name": "Canan Dağ",
            "email": "canan@example.com",
            "department": "Tıp",
            "graduation_year": 2018,
        }
        _, _, create_data = self._run_request("POST", "/api/users", body=payload)
        user_id = create_data["data"]["id"]

        del_status, _, del_data = self._run_request(
            "DELETE", f"/api/users/{user_id}"
        )
        self.assertEqual(del_status, 200)
        self.assertEqual(del_data["status"], "success")
        self.assertIn("deleted successfully", del_data["message"])

        get_status, _, _ = self._run_request("GET", f"/api/users/{user_id}")
        self.assertEqual(get_status, 404)

        del_missing_status, _, del_missing_data = self._run_request(
            "DELETE", "/api/users/999"
        )
        self.assertEqual(del_missing_status, 404)
        self.assertEqual(del_missing_data["status"], "error")

    # -------------------------------------------------------------------------
    # Web View Routes (app/api/web_routes.py -> UserController & Jinja2 Templates)
    # -------------------------------------------------------------------------

    def test_web_landing_and_about_pages(self):
        """GET / and /about should return 200 HTML content."""
        status_root, _, body_root = self._run_request("GET", "/")
        self.assertEqual(status_root, 200)
        self.assertIn("<!DOCTYPE html>", body_root)

        status_about, _, body_about = self._run_request("GET", "/about")
        self.assertEqual(status_about, 200)
        self.assertIn("<!DOCTYPE html>", body_about)

    # 1. READ - LIST
    def test_web_get_users_empty_state(self):
        """GET /users with no users should render HTML with 'No users found' message."""
        status_code, headers, html = self._run_request("GET", "/users")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Alumni List", html)
        self.assertIn("No users found", html)
        # Verify create user form elements exist
        self.assertIn('name="name"', html)
        self.assertIn('name="email"', html)
        self.assertIn('name="department"', html)
        self.assertIn('name="graduation_year"', html)

    def test_web_get_users_with_existing_users(self):
        """GET /users with existing users should render table with user details and actions."""
        UserController.create_user(
            name="Ece Bilgin",
            email="ece@alumni.istanbul.edu.tr",
            department="Matematik",
            graduation_year=2021,
        )

        status_code, headers, html = self._run_request("GET", "/users")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Ece Bilgin", html)
        self.assertIn("ece@alumni.istanbul.edu.tr", html)
        self.assertIn("Matematik", html)
        self.assertIn("2021", html)
        self.assertNotIn("No users found", html)
        # Verify action links exist
        self.assertIn('href="/users/1"', html)
        self.assertIn('href="/users/1/edit"', html)
        self.assertIn('action="/users/1/delete"', html)

    # 2. CREATE
    def test_web_post_users_form_submission(self):
        """POST /users with urlencoded form should create user and return updated list View."""
        form_payload = {
            "name": "Caner Öztürk",
            "email": "caner@alumni.istanbul.edu.tr",
            "department": "Kimya",
            "graduation_year": "2023",
        }
        status_code, headers, html = self._run_request(
            "POST",
            "/users",
            body=form_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Kullanıcı başarıyla oluşturuldu", html)
        self.assertIn("Caner Öztürk", html)
        self.assertIn("caner@alumni.istanbul.edu.tr", html)
        self.assertIn("Kimya", html)
        self.assertIn("2023", html)

        # Verify that subsequent GET /users also renders the newly created user
        get_status, _, get_html = self._run_request("GET", "/users")
        self.assertEqual(get_status, 200)
        self.assertIn("Caner Öztürk", get_html)
        self.assertNotIn("No users found", get_html)

    def test_web_post_users_json_submission(self):
        """POST /users with JSON payload should also create user and return updated View."""
        json_payload = {
            "name": "Seda Varol",
            "email": "seda@alumni.istanbul.edu.tr",
            "department": "Biyoloji",
            "graduation_year": 2022,
        }
        status_code, headers, html = self._run_request(
            "POST",
            "/users",
            body=json_payload,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Seda Varol", html)
        self.assertIn("seda@alumni.istanbul.edu.tr", html)
        self.assertIn("Biyoloji", html)

    def test_web_post_users_validation_error(self):
        """POST /users with invalid data should return 400 with error message on View."""
        invalid_payload = {
            "name": "Time Traveler",
            "email": "timetraveler@example.com",
            "department": "Physics",
            "graduation_year": "1800",  # Out of range (< 1900)
        }
        status_code, headers, html = self._run_request(
            "POST",
            "/users",
            body=invalid_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 400)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("alert-error", html)

    # 3. READ - SINGLE USER (DETAIL)
    def test_web_get_user_detail_existing(self):
        """GET /users/{id} for existing user should render detail View with user profile."""
        create_res = UserController.create_user(
            name="Hande Demir",
            email="hande@alumni.istanbul.edu.tr",
            department="Psikoloji",
            graduation_year=2021,
        )
        user_id = create_res["user"].id

        status_code, headers, html = self._run_request("GET", f"/users/{user_id}")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Hande Demir", html)
        self.assertIn("hande@alumni.istanbul.edu.tr", html)
        self.assertIn("Psikoloji", html)
        self.assertIn("2021", html)
        # Verify navigation and action links
        self.assertIn('href="/users"', html)
        self.assertIn(f'href="/users/{user_id}/edit"', html)
        self.assertIn(f'action="/users/{user_id}/delete"', html)

    def test_web_get_user_detail_missing(self):
        """GET /users/{id} for non-existent user should return 404 with not-found View."""
        status_code, headers, html = self._run_request("GET", "/users/999")
        self.assertEqual(status_code, 404)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Kullanıcı Bulunamadı", html)

    # 4. UPDATE - EDIT FORM & POST
    def test_web_get_user_edit_form_existing(self):
        """GET /users/{id}/edit for existing user should render pre-filled edit form."""
        create_res = UserController.create_user(
            name="Kemal Sunal",
            email="kemal@alumni.istanbul.edu.tr",
            department="İletişim",
            graduation_year=2019,
        )
        user_id = create_res["user"].id

        status_code, headers, html = self._run_request("GET", f"/users/{user_id}/edit")
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn('value="Kemal Sunal"', html)
        self.assertIn('value="kemal@alumni.istanbul.edu.tr"', html)
        self.assertIn('value="İletişim"', html)
        self.assertIn('value="2019"', html)
        self.assertIn(f'action="/users/{user_id}/edit"', html)

    def test_web_get_user_edit_form_missing(self):
        """GET /users/{id}/edit for missing user should return 404 not-found View."""
        status_code, headers, html = self._run_request("GET", "/users/999/edit")
        self.assertEqual(status_code, 404)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Kullanıcı Bulunamadı", html)

    def test_web_update_user_form_post(self):
        """POST /users/{id}/edit should update user and render detail View with success message."""
        create_res = UserController.create_user(
            name="Zeynep Kaya",
            email="zeynep@old.com",
            department="Sosyoloji",
            graduation_year=2020,
        )
        user_id = create_res["user"].id

        update_payload = {
            "name": "Zeynep Kaya",
            "email": "zeynep@new.com",
            "department": "Felsefe",
            "graduation_year": "2021",
        }
        status_code, headers, html = self._run_request(
            "POST",
            f"/users/{user_id}/edit",
            body=update_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Kullanıcı başarıyla güncellendi", html)
        self.assertIn("zeynep@new.com", html)
        self.assertIn("Felsefe", html)
        self.assertIn("2021", html)

        # Verify update persists in detail view
        get_status, _, get_html = self._run_request("GET", f"/users/{user_id}")
        self.assertEqual(get_status, 200)
        self.assertIn("zeynep@new.com", get_html)
        self.assertIn("Felsefe", get_html)

    def test_web_update_user_put(self):
        """PUT /users/{id} should update user and return JSON when requested."""
        create_res = UserController.create_user(
            name="Burak Çelik",
            email="burak@test.com",
            department="Jeoloji",
            graduation_year=2020,
        )
        user_id = create_res["user"].id

        status_put, _, data_put = self._run_request(
            "PUT",
            f"/users/{user_id}",
            body={"department": "Jeofizik"},
            headers={"accept": "application/json"},
        )
        self.assertEqual(status_put, 200)
        self.assertTrue(data_put["success"])
        self.assertEqual(data_put["user"]["department"], "Jeofizik")

    def test_web_update_user_missing(self):
        """Updating non-existent user should return 404."""
        status_code, _, _ = self._run_request(
            "POST",
            "/users/999/edit",
            body={"name": "Ghost", "email": "ghost@ghost.com", "department": "CS", "graduation_year": 2024},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 404)

        status_put, _, data_put = self._run_request(
            "PUT",
            "/users/999",
            body={"department": "Physics"},
            headers={"accept": "application/json"},
        )
        self.assertEqual(status_put, 404)
        self.assertFalse(data_put["success"])

    def test_web_update_user_validation_error(self):
        """POST /users/{id}/edit with invalid data should return 400 edit View."""
        create_res = UserController.create_user(
            name="Ozan Mert",
            email="ozan@test.com",
            department="İktisat",
            graduation_year=2018,
        )
        user_id = create_res["user"].id

        status_code, _, html = self._run_request(
            "POST",
            f"/users/{user_id}/edit",
            body={"name": "Ozan Mert", "email": "ozan@test.com", "department": "İktisat", "graduation_year": 1850},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 400)
        self.assertIn("alert-error", html)

    # 5. DELETE
    def test_web_delete_user_form_post(self):
        """POST /users/{id}/delete should delete user and render list View with success message."""
        create_res = UserController.create_user(
            name="Gizem Kurt",
            email="gizem@alumni.istanbul.edu.tr",
            department="Hukuk",
            graduation_year=2022,
        )
        user_id = create_res["user"].id

        status_code, headers, html = self._run_request(
            "POST",
            f"/users/{user_id}/delete",
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("başarıyla silindi", html)

        # Subsequent GET should return 404
        get_status, _, _ = self._run_request("GET", f"/users/{user_id}")
        self.assertEqual(get_status, 404)

    def test_web_delete_user_http_delete(self):
        """DELETE /users/{id} should delete user and return JSON when requested."""
        create_res = UserController.create_user(
            name="Tuna Demir",
            email="tuna@test.com",
            department="Tıp",
            graduation_year=2020,
        )
        user_id = create_res["user"].id

        status_del, _, data_del = self._run_request(
            "DELETE",
            f"/users/{user_id}",
            headers={"accept": "application/json"},
        )
        self.assertEqual(status_del, 200)
        self.assertTrue(data_del["success"])
        self.assertIn("deleted successfully", data_del["message"])

    def test_web_delete_user_missing(self):
        """Deleting non-existent user should return 404."""
        status_post, _, html = self._run_request("POST", "/users/999/delete")
        self.assertEqual(status_post, 404)
        self.assertTrue("not found" in html.lower() or "bulunamadı" in html.lower())

        status_del, _, data_del = self._run_request(
            "DELETE",
            "/users/999",
            headers={"accept": "application/json"},
        )
        self.assertEqual(status_del, 404)
        self.assertFalse(data_del["success"])

    # 6. FULL CRUD LIFECYCLE
    def test_web_crud_full_lifecycle(self):
        """Verifies complete Create -> Read -> Update -> Delete flow through Web Views."""
        # Step 1: Create user via form
        create_payload = {
            "name": "Arda Güler",
            "email": "arda@alumni.istanbul.edu.tr",
            "department": "Spor Bilimleri",
            "graduation_year": "2023",
        }
        create_status, _, create_html = self._run_request(
            "POST",
            "/users",
            body=create_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(create_status, 200)
        self.assertIn("Arda Güler", create_html)

        # Step 2: Read list
        list_status, _, list_html = self._run_request("GET", "/users")
        self.assertEqual(list_status, 200)
        self.assertIn("Arda Güler", list_html)
        self.assertIn("Spor Bilimleri", list_html)

        # Step 3: Read single detail
        detail_status, _, detail_html = self._run_request("GET", "/users/1")
        self.assertEqual(detail_status, 200)
        self.assertIn("Arda Güler", detail_html)
        self.assertIn("arda@alumni.istanbul.edu.tr", detail_html)

        # Step 4: Read edit form
        edit_status, _, edit_html = self._run_request("GET", "/users/1/edit")
        self.assertEqual(edit_status, 200)
        self.assertIn('value="Arda Güler"', edit_html)

        # Step 5: Update via edit form
        update_payload = {
            "name": "Arda Güler",
            "email": "arda.real@alumni.istanbul.edu.tr",
            "department": "Antrenörlük",
            "graduation_year": "2024",
        }
        update_status, _, update_html = self._run_request(
            "POST",
            "/users/1/edit",
            body=update_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(update_status, 200)
        self.assertIn("arda.real@alumni.istanbul.edu.tr", update_html)
        self.assertIn("Antrenörlük", update_html)

        # Step 6: Verify updated detail
        detail2_status, _, detail2_html = self._run_request("GET", "/users/1")
        self.assertEqual(detail2_status, 200)
        self.assertIn("arda.real@alumni.istanbul.edu.tr", detail2_html)

        # Step 7: Delete user
        del_status, _, del_html = self._run_request("POST", "/users/1/delete")
        self.assertEqual(del_status, 200)
        self.assertIn("başarıyla silindi", del_html)

        # Step 8: Verify user removed from list and detail
        final_list_status, _, final_list_html = self._run_request("GET", "/users")
        self.assertEqual(final_list_status, 200)
        self.assertIn("No users found", final_list_html)

        final_detail_status, _, _ = self._run_request("GET", "/users/1")
        self.assertEqual(final_detail_status, 404)

    # -------------------------------------------------------------------------
    # Existing Routes Integrity Check
    # -------------------------------------------------------------------------

    def test_health_and_test_routes_preserved(self):
        """Preserved existing routes (/api/health, /hello, /sum) should continue working."""
        status_health, _, data_health = self._run_request("GET", "/api/health")
        self.assertEqual(status_health, 200)
        self.assertEqual(data_health, {"status": "ok"})

        status_hello, _, data_hello = self._run_request("GET", "/hello")
        self.assertEqual(status_hello, 200)
        self.assertEqual(data_hello, {"message": "Hello, World!"})

        status_name, _, data_name = self._run_request("GET", "/hello/Antigravity")
        self.assertEqual(status_name, 200)
        self.assertEqual(data_name, {"message": "Hello, Antigravity!"})

        status_sum, _, data_sum = self._run_request("GET", "/sum/15/27")
        self.assertEqual(status_sum, 200)
        self.assertEqual(data_sum["result"], 42)


if __name__ == "__main__":
    unittest.main()
