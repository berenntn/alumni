"""Unit and integration tests for User, ApiUser, Web, and Health routes via ASGI."""

import asyncio
import json
import unittest
from typing import Any, Dict, Optional, Tuple

from app.main import app
from app.services.user_service import clear_users


class TestRoutes(unittest.TestCase):
    """Test suite verifying route-to-controller integration and HTTP endpoints."""

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
                    for k, v in (headers or {}).items()
                ],
            }

            body_bytes = b""
            if body is not None:
                body_bytes = json.dumps(body).encode("utf-8")
                scope["headers"].append((b"content-type", b"application/json"))
            scope["headers"].append(
                (b"content-length", str(len(body_bytes)).encode("latin-1"))
            )

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
            content_type = response_headers.get("content-type", "")
            if "application/json" in content_type:
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
        # Create user first
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

        # Fetch existing user
        get_status, _, get_data = self._run_request("GET", f"/api/users/{user_id}")
        self.assertEqual(get_status, 200)
        self.assertEqual(get_data["status"], "success")
        self.assertEqual(get_data["data"]["name"], "Ayşe Yılmaz")

        # Fetch non-existent user
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

        # Full update
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

        # Update non-existent user
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

        # Partial update: only email
        patch_status, _, patch_data = self._run_request(
            "PATCH", f"/api/users/{user_id}", body={"email": "selin@new.com"}
        )
        self.assertEqual(patch_status, 200)
        self.assertEqual(patch_data["status"], "success")
        self.assertEqual(patch_data["data"]["email"], "selin@new.com")
        self.assertEqual(patch_data["data"]["name"], "Selin Kaya")  # Preserved

        # Patch non-existent user
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

        # Successful deletion
        del_status, _, del_data = self._run_request(
            "DELETE", f"/api/users/{user_id}"
        )
        self.assertEqual(del_status, 200)
        self.assertEqual(del_data["status"], "success")
        self.assertIn("deleted successfully", del_data["message"])

        # Subsequent fetch returns 404
        get_status, _, _ = self._run_request("GET", f"/api/users/{user_id}")
        self.assertEqual(get_status, 404)

        # Deleting non-existent user returns 404
        del_missing_status, _, del_missing_data = self._run_request(
            "DELETE", "/api/users/999"
        )
        self.assertEqual(del_missing_status, 404)
        self.assertEqual(del_missing_data["status"], "error")

    # -------------------------------------------------------------------------
    # Web Routes (app/api/web_routes.py -> UserController)
    # -------------------------------------------------------------------------

    def test_web_landing_and_about_pages(self):
        """GET / and /about should return 200 HTML content."""
        status_root, _, body_root = self._run_request("GET", "/")
        self.assertEqual(status_root, 200)
        self.assertIn("<!DOCTYPE html>", body_root)

        status_about, _, body_about = self._run_request("GET", "/about")
        self.assertEqual(status_about, 200)
        self.assertIn("<!DOCTYPE html>", body_about)

    def test_web_user_crud_endpoints(self):
        """Web user endpoints (/users) should invoke UserController successfully."""
        # List users (empty)
        status_get_all, _, data_all = self._run_request("GET", "/users")
        self.assertEqual(status_get_all, 200)
        self.assertTrue(data_all["success"])
        self.assertEqual(data_all["count"], 0)

        # Create web user
        create_payload = {
            "name": "Web Test User",
            "email": "webuser@example.com",
            "department": "Felsefe",
            "graduation_year": 2021,
        }
        status_post, _, data_post = self._run_request(
            "POST", "/users", body=create_payload
        )
        self.assertEqual(status_post, 200)
        self.assertTrue(data_post["success"])
        self.assertEqual(data_post["user"]["name"], "Web Test User")

        # Get web user by ID
        status_get, _, data_get = self._run_request("GET", "/users/1")
        self.assertEqual(status_get, 200)
        self.assertTrue(data_get["success"])
        self.assertEqual(data_get["user"]["name"], "Web Test User")

        # Update web user
        status_put, _, data_put = self._run_request(
            "PUT", "/users/1", body={"email": "updated_web@example.com"}
        )
        self.assertEqual(status_put, 200)
        self.assertTrue(data_put["success"])
        self.assertEqual(data_put["user"]["email"], "updated_web@example.com")

        # Delete web user
        status_del, _, data_del = self._run_request("DELETE", "/users/1")
        self.assertEqual(status_del, 200)
        self.assertTrue(data_del["success"])
        self.assertIn("deleted successfully", data_del["message"])

    # -------------------------------------------------------------------------
    # Existing Routes Integrity Check
    # -------------------------------------------------------------------------

    def test_health_and_test_routes_preserved(self):
        """Preserved existing routes (/api/health, /hello, /sum) should continue working."""
        # Health check
        status_health, _, data_health = self._run_request("GET", "/api/health")
        self.assertEqual(status_health, 200)
        self.assertEqual(data_health, {"status": "ok"})

        # Hello endpoint
        status_hello, _, data_hello = self._run_request("GET", "/hello")
        self.assertEqual(status_hello, 200)
        self.assertEqual(data_hello, {"message": "Hello, World!"})

        # Hello with path parameter
        status_name, _, data_name = self._run_request("GET", "/hello/Antigravity")
        self.assertEqual(status_name, 200)
        self.assertEqual(data_name, {"message": "Hello, Antigravity!"})

        # Sum calculation endpoint
        status_sum, _, data_sum = self._run_request("GET", "/sum/15/27")
        self.assertEqual(status_sum, 200)
        self.assertEqual(data_sum["result"], 42)


if __name__ == "__main__":
    unittest.main()
