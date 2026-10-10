"""Unit and integration tests for Announcement Web and REST API routes via ASGI."""

import asyncio
import json
import unittest
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from app.controllers.announcement_controller import AnnouncementController
from app.main import app
from app.services.announcement_service import clear_announcements


class TestAnnouncementRoutes(unittest.TestCase):
    """Test suite verifying Announcement route-to-controller integration and HTTP endpoints."""

    def setUp(self):
        """Reset the in-memory announcement store before each test."""
        clear_announcements()

    def tearDown(self):
        """Clean up in-memory announcement store after each test."""
        clear_announcements()

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
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("ascii"),
                "query_string": b"",
                "headers": [
                    (k.lower().encode("latin1"), v.encode("latin1"))
                    for k, v in req_headers.items()
                ],
            }

            status_code = 0
            resp_headers: Dict[str, str] = {}
            resp_body_chunks = []

            async def receive():
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }

            async def send(message):
                nonlocal status_code, resp_headers
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    for k, v in message.get("headers", []):
                        resp_headers[k.decode("latin1").lower()] = v.decode("latin1")
                elif message["type"] == "http.response.body":
                    resp_body_chunks.append(message.get("body", b""))

            await app(scope, receive, send)

            raw_body = b"".join(resp_body_chunks).decode("utf-8")
            try:
                parsed_body = json.loads(raw_body)
            except Exception:
                parsed_body = raw_body

            return status_code, resp_headers, parsed_body

        return asyncio.run(_asgi_call())

    # =========================================================================
    # REST API Announcement Routes (/api/announcements -> ApiAnnouncementController)
    # =========================================================================

    def test_api_get_announcements_empty(self):
        """GET /api/announcements should return 200 with empty announcement list."""
        status_code, _, data = self._run_request("GET", "/api/announcements")
        self.assertEqual(status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["data"], [])

    def test_api_create_announcement(self):
        """POST /api/announcements should return 201 Created and announcement data."""
        payload = {
            "title": "Mezunlar Buluşması 2026",
            "content": "Geleneksel mezunlar günü 15 Mayıs'ta yapılacaktır.",
            "created_by": 1,
        }
        status_code, _, data = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        self.assertEqual(status_code, 201)
        self.assertEqual(data["status"], "success")
        self.assertIn("Announcement created successfully", data["message"])
        self.assertIsNotNone(data["data"])
        self.assertEqual(data["data"]["id"], 1)
        self.assertEqual(data["data"]["title"], "Mezunlar Buluşması 2026")
        self.assertEqual(data["data"]["created_by"], 1)

    def test_api_create_announcement_validation_error(self):
        """POST /api/announcements with invalid data should return 422 Unprocessable Entity."""
        payload = {
            "title": "",  # Empty string violates min_length=1
            "content": "İçerik",
        }
        status_code, _, _ = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        self.assertEqual(status_code, 422)

    def test_api_get_announcement_by_id(self):
        """GET /api/announcements/{id} should return 200 for existing announcement and 404 for missing."""
        payload = {
            "title": "Kariyer Semineri",
            "content": "Yapay zeka ve veri bilimi kariyer semineri.",
            "created_by": 2,
        }
        create_status, _, create_data = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        self.assertEqual(create_status, 201)
        announcement_id = create_data["data"]["id"]

        # Existing announcement
        get_status, _, get_data = self._run_request(
            "GET", f"/api/announcements/{announcement_id}"
        )
        self.assertEqual(get_status, 200)
        self.assertEqual(get_data["status"], "success")
        self.assertEqual(get_data["data"]["title"], "Kariyer Semineri")

        # Missing announcement
        missing_status, _, missing_data = self._run_request(
            "GET", "/api/announcements/999"
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")
        self.assertIn("not found", missing_data["message"])

    def test_api_update_announcement_put(self):
        """PUT /api/announcements/{id} should return 200 on full update and 404 when missing."""
        payload = {
            "title": "Eski Başlık",
            "content": "Eski duyuru açıklaması.",
            "created_by": 3,
        }
        _, _, create_data = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        announcement_id = create_data["data"]["id"]

        update_payload = {
            "title": "Güncel Başlık",
            "content": "Tamamen güncellenmiş duyuru açıklaması.",
            "created_by": 3,
        }
        put_status, _, put_data = self._run_request(
            "PUT", f"/api/announcements/{announcement_id}", body=update_payload
        )
        self.assertEqual(put_status, 200)
        self.assertEqual(put_data["status"], "success")
        self.assertEqual(put_data["data"]["title"], "Güncel Başlık")
        self.assertEqual(
            put_data["data"]["content"],
            "Tamamen güncellenmiş duyuru açıklaması.",
        )

        missing_status, _, missing_data = self._run_request(
            "PUT", "/api/announcements/999", body=update_payload
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")

    def test_api_patch_announcement(self):
        """PATCH /api/announcements/{id} should return 200 on partial update and 404 when missing."""
        payload = {
            "title": "Bahar Konseri",
            "content": "Bahar şenliği konser programı.",
            "created_by": 4,
        }
        _, _, create_data = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        announcement_id = create_data["data"]["id"]

        patch_status, _, patch_data = self._run_request(
            "PATCH",
            f"/api/announcements/{announcement_id}",
            body={"title": "Bahar Festivali Konseri"},
        )
        self.assertEqual(patch_status, 200)
        self.assertEqual(patch_data["status"], "success")
        self.assertEqual(patch_data["data"]["title"], "Bahar Festivali Konseri")
        self.assertEqual(
            patch_data["data"]["content"], "Bahar şenliği konser programı."
        )

        missing_status, _, missing_data = self._run_request(
            "PATCH", "/api/announcements/999", body={"title": "Hayalet"}
        )
        self.assertEqual(missing_status, 404)
        self.assertEqual(missing_data["status"], "error")

    def test_api_delete_announcement(self):
        """DELETE /api/announcements/{id} should return 200 on deletion and 404 when missing."""
        payload = {
            "title": "Silinecek Duyuru",
            "content": "Silinecek metin.",
            "created_by": 5,
        }
        _, _, create_data = self._run_request(
            "POST", "/api/announcements", body=payload
        )
        announcement_id = create_data["data"]["id"]

        del_status, _, del_data = self._run_request(
            "DELETE", f"/api/announcements/{announcement_id}"
        )
        self.assertEqual(del_status, 200)
        self.assertEqual(del_data["status"], "success")
        self.assertIn("deleted successfully", del_data["message"])

        # Subsequent GET should return 404
        get_status, _, _ = self._run_request(
            "GET", f"/api/announcements/{announcement_id}"
        )
        self.assertEqual(get_status, 404)

        del_missing_status, _, del_missing_data = self._run_request(
            "DELETE", "/api/announcements/999"
        )
        self.assertEqual(del_missing_status, 404)
        self.assertEqual(del_missing_data["status"], "error")

    # =========================================================================
    # Web Announcement Routes (/announcements -> AnnouncementController)
    # =========================================================================

    def test_web_get_announcements_empty(self):
        """GET /announcements should return 200 with empty count via AnnouncementController."""
        status_code, _, data = self._run_request("GET", "/announcements")
        self.assertEqual(status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["announcements"], [])

    def test_web_create_announcement(self):
        """POST /announcements should create announcement and return success=True."""
        payload = {
            "title": "Web Duyurusu",
            "content": "Web arayüzü üzerinden oluşturulan duyuru içeriği.",
            "created_by": 10,
        }
        status_code, _, data = self._run_request(
            "POST", "/announcements", body=payload
        )
        self.assertEqual(status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["announcement"]["title"], "Web Duyurusu")
        self.assertEqual(data["announcement"]["id"], 1)

    def test_web_create_announcement_invalid(self):
        """POST /announcements with empty title should return 400 Bad Request."""
        payload = {
            "title": "",
            "content": "İçerik var ama başlık boş.",
        }
        status_code, _, data = self._run_request(
            "POST", "/announcements", body=payload
        )
        self.assertEqual(status_code, 400)
        self.assertFalse(data["success"])

    def test_web_get_announcement_by_id(self):
        """GET /announcements/{id} should return 200 for existing and 404 for missing."""
        payload = {
            "title": "Tekil Web Duyurusu",
            "content": "Tekil duyuru metni.",
            "created_by": 2,
        }
        create_status, _, create_data = self._run_request(
            "POST", "/announcements", body=payload
        )
        self.assertEqual(create_status, 200)
        announcement_id = create_data["announcement"]["id"]

        get_status, _, get_data = self._run_request(
            "GET", f"/announcements/{announcement_id}"
        )
        self.assertEqual(get_status, 200)
        self.assertTrue(get_data["success"])
        self.assertEqual(get_data["announcement"]["title"], "Tekil Web Duyurusu")

        missing_status, _, missing_data = self._run_request(
            "GET", "/announcements/999"
        )
        self.assertEqual(missing_status, 404)
        self.assertFalse(missing_data["success"])

    def test_web_update_announcement(self):
        """PUT /announcements/{id} should update announcement and return success."""
        payload = {
            "title": "Başlangıç Başlığı",
            "content": "Başlangıç içeriği.",
            "created_by": 3,
        }
        _, _, create_data = self._run_request(
            "POST", "/announcements", body=payload
        )
        announcement_id = create_data["announcement"]["id"]

        update_payload = {
            "title": "Güncellenmiş Web Başlığı",
            "content": "Güncellenmiş web içeriği.",
        }
        put_status, _, put_data = self._run_request(
            "PUT", f"/announcements/{announcement_id}", body=update_payload
        )
        self.assertEqual(put_status, 200)
        self.assertTrue(put_data["success"])
        self.assertEqual(
            put_data["announcement"]["title"], "Güncellenmiş Web Başlığı"
        )

        missing_status, _, missing_data = self._run_request(
            "PUT", "/announcements/999", body=update_payload
        )
        self.assertEqual(missing_status, 404)
        self.assertFalse(missing_data["success"])

    def test_web_delete_announcement(self):
        """DELETE /announcements/{id} should delete announcement and return success."""
        payload = {
            "title": "Kaldırılacak Web Duyurusu",
            "content": "Kaldırılacak içerik.",
            "created_by": 4,
        }
        _, _, create_data = self._run_request(
            "POST", "/announcements", body=payload
        )
        announcement_id = create_data["announcement"]["id"]

        del_status, _, del_data = self._run_request(
            "DELETE", f"/announcements/{announcement_id}"
        )
        self.assertEqual(del_status, 200)
        self.assertTrue(del_data["success"])
        self.assertIn("deleted successfully", del_data["message"])

        # Check subsequent GET is 404
        get_status, _, _ = self._run_request(
            "GET", f"/announcements/{announcement_id}"
        )
        self.assertEqual(get_status, 404)

        missing_status, _, missing_data = self._run_request(
            "DELETE", "/announcements/999"
        )
        self.assertEqual(missing_status, 404)
        self.assertFalse(missing_data["success"])

    # =========================================================================
    # Web Announcement View Interface Tests (Jinja2 HTML Templates)
    # =========================================================================

    def test_web_get_announcements_html_empty_state(self):
        """GET /announcements with text/html should render HTML listing with 'No announcements found'."""
        status_code, headers, html = self._run_request(
            "GET", "/announcements", headers={"accept": "text/html"}
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Announcements", html)
        self.assertIn("Duyurular", html)
        self.assertIn("No announcements found", html)
        # Check form inputs exist
        self.assertIn('name="title"', html)
        self.assertIn('name="content"', html)
        self.assertIn('name="created_by"', html)

    def test_web_get_announcements_html_with_data(self):
        """GET /announcements with text/html should list existing announcements with action buttons."""
        AnnouncementController.create_announcement(
            {
                "title": "Bahar Festivali Başlıyor",
                "content": "Bahar festivali etkinlikleri kampüste düzenlenecektir.",
                "created_by": 1,
            }
        )
        status_code, headers, html = self._run_request(
            "GET", "/announcements", headers={"accept": "text/html"}
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Bahar Festivali Başlıyor", html)
        self.assertNotIn("No announcements found", html)
        # Check actions exist
        self.assertIn('href="/announcements/1"', html)
        self.assertIn('href="/announcements/1/edit"', html)
        self.assertIn('action="/announcements/1/delete"', html)

    def test_web_post_announcements_form_submission(self):
        """POST /announcements with form payload should create announcement and return updated list View."""
        form_payload = {
            "title": "Staj Başvuruları Açıldı",
            "content": "Yaz dönemi staj başvuruları kariyer merkezine yapılacaktır.",
            "created_by": "2",
        }
        status_code, headers, html = self._run_request(
            "POST",
            "/announcements",
            body=form_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Duyuru başarıyla yayınlandı", html)
        self.assertIn("Staj Başvuruları Açıldı", html)

    def test_web_post_announcements_form_validation_error(self):
        """POST /announcements with empty title should return 400 with alert on list View."""
        invalid_payload = {
            "title": "",
            "content": "Başlık boş olan duyuru metni.",
        }
        status_code, headers, html = self._run_request(
            "POST",
            "/announcements",
            body=invalid_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 400)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("alert-error", html)

    def test_web_get_announcement_detail_html_existing(self):
        """GET /announcements/{id} with text/html should render detail page."""
        create_res = AnnouncementController.create_announcement(
            {
                "title": "Kütüphane Çalışma Saatleri",
                "content": "Merkez kütüphane vize haftasında 7/24 açıktır.",
                "created_by": 5,
            }
        )
        ann_id = create_res["announcement"].id

        status_code, headers, html = self._run_request(
            "GET", f"/announcements/{ann_id}", headers={"accept": "text/html"}
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Kütüphane Çalışma Saatleri", html)
        self.assertIn("Merkez kütüphane vize haftasında 7/24 açıktır.", html)
        self.assertIn('href="/announcements"', html)
        self.assertIn(f'href="/announcements/{ann_id}/edit"', html)
        self.assertIn(f'action="/announcements/{ann_id}/delete"', html)

    def test_web_get_announcement_detail_html_missing(self):
        """GET /announcements/999 with text/html should return 404 not found page."""
        status_code, headers, html = self._run_request(
            "GET", "/announcements/999", headers={"accept": "text/html"}
        )
        self.assertEqual(status_code, 404)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Duyuru Bulunamadı", html)

    def test_web_get_announcement_edit_form_existing(self):
        """GET /announcements/{id}/edit should render prefilled edit form."""
        create_res = AnnouncementController.create_announcement(
            {
                "title": "Eski Seminer Duyurusu",
                "content": "Eski duyuru açıklaması.",
                "created_by": 3,
            }
        )
        ann_id = create_res["announcement"].id

        status_code, headers, html = self._run_request(
            "GET", f"/announcements/{ann_id}/edit"
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn('value="Eski Seminer Duyurusu"', html)
        self.assertIn("Eski duyuru açıklaması.", html)
        self.assertIn(f'action="/announcements/{ann_id}/edit"', html)

    def test_web_get_announcement_edit_form_missing(self):
        """GET /announcements/999/edit should return 404."""
        status_code, headers, html = self._run_request(
            "GET", "/announcements/999/edit"
        )
        self.assertEqual(status_code, 404)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Duyuru Bulunamadı", html)

    def test_web_update_announcement_form_post(self):
        """POST /announcements/{id}/edit should update announcement and render detail view."""
        create_res = AnnouncementController.create_announcement(
            {
                "title": "Güncellenecek Duyuru",
                "content": "Eski açıklama metni.",
                "created_by": 4,
            }
        )
        ann_id = create_res["announcement"].id

        update_payload = {
            "title": "Yepyeni Güncellenmiş Duyuru",
            "content": "Yenilenmiş açıklama metni.",
            "created_by": "4",
        }
        status_code, headers, html = self._run_request(
            "POST",
            f"/announcements/{ann_id}/edit",
            body=update_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("Duyuru başarıyla güncellendi", html)
        self.assertIn("Yepyeni Güncellenmiş Duyuru", html)
        self.assertIn("Yenilenmiş açıklama metni.", html)

    def test_web_update_announcement_form_validation_error(self):
        """POST /announcements/{id}/edit with empty title should return 400 edit view."""
        create_res = AnnouncementController.create_announcement(
            {
                "title": "İlk Duyuru",
                "content": "İlk içerik.",
                "created_by": 1,
            }
        )
        ann_id = create_res["announcement"].id

        status_code, _, html = self._run_request(
            "POST",
            f"/announcements/{ann_id}/edit",
            body={"title": "", "content": "İçerik var fakat başlık yok."},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 400)
        self.assertIn("alert-error", html)

    def test_web_update_announcement_form_missing(self):
        """POST /announcements/999/edit should return 404."""
        status_code, _, html = self._run_request(
            "POST",
            "/announcements/999/edit",
            body={"title": "Hayalet", "content": "Hayalet içerik"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status_code, 404)
        self.assertIn("Duyuru Bulunamadı", html)

    def test_web_delete_announcement_form_post(self):
        """POST /announcements/{id}/delete should delete announcement and render list view."""
        create_res = AnnouncementController.create_announcement(
            {
                "title": "Silinecek Duyuru Form",
                "content": "Bu duyuru silinecektir.",
                "created_by": 1,
            }
        )
        ann_id = create_res["announcement"].id

        status_code, headers, html = self._run_request(
            "POST", f"/announcements/{ann_id}/delete"
        )
        self.assertEqual(status_code, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("başarıyla silindi", html)

        # Confirm 404 on subsequent detail GET
        get_status, _, _ = self._run_request(
            "GET", f"/announcements/{ann_id}", headers={"accept": "text/html"}
        )
        self.assertEqual(get_status, 404)

    def test_web_delete_announcement_form_missing(self):
        """POST /announcements/999/delete should return 404."""
        status_code, _, html = self._run_request("POST", "/announcements/999/delete")
        self.assertEqual(status_code, 404)
        self.assertTrue("bulunamadı" in html.lower() or "not found" in html.lower())

    def test_web_announcement_full_crud_lifecycle(self):
        """Verifies complete Create -> Read List -> Read Detail -> Edit -> Update -> Delete HTML workflow."""
        # Step 1: Create announcement via form
        create_payload = {
            "title": "2026 Mezuniyet Töreni Programı",
            "content": "Mezuniyet töreni 25 Haziran saat 14:00'te ana amfide yapılacaktır.",
            "created_by": "1",
        }
        create_status, _, create_html = self._run_request(
            "POST",
            "/announcements",
            body=create_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(create_status, 200)
        self.assertIn("2026 Mezuniyet Töreni Programı", create_html)

        # Step 2: Read list View
        list_status, _, list_html = self._run_request(
            "GET", "/announcements", headers={"accept": "text/html"}
        )
        self.assertEqual(list_status, 200)
        self.assertIn("2026 Mezuniyet Töreni Programı", list_html)
        self.assertNotIn("No announcements found", list_html)

        # Step 3: Read detail View
        detail_status, _, detail_html = self._run_request(
            "GET", "/announcements/1", headers={"accept": "text/html"}
        )
        self.assertEqual(detail_status, 200)
        self.assertIn("2026 Mezuniyet Töreni Programı", detail_html)
        self.assertIn("Mezuniyet töreni 25 Haziran", detail_html)

        # Step 4: Read edit form View
        edit_status, _, edit_html = self._run_request("GET", "/announcements/1/edit")
        self.assertEqual(edit_status, 200)
        self.assertIn('value="2026 Mezuniyet Töreni Programı"', edit_html)

        # Step 5: Update via edit form
        update_payload = {
            "title": "2026 Mezuniyet Töreni Programı (Revize)",
            "content": "Tören saati 15:00 olarak güncellenmiştir.",
            "created_by": "1",
        }
        update_status, _, update_html = self._run_request(
            "POST",
            "/announcements/1/edit",
            body=update_payload,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(update_status, 200)
        self.assertIn("2026 Mezuniyet Töreni Programı (Revize)", update_html)
        self.assertIn("Tören saati 15:00 olarak güncellenmiştir.", update_html)

        # Step 6: Verify updated detail
        detail2_status, _, detail2_html = self._run_request(
            "GET", "/announcements/1", headers={"accept": "text/html"}
        )
        self.assertEqual(detail2_status, 200)
        self.assertIn("2026 Mezuniyet Töreni Programı (Revize)", detail2_html)

        # Step 7: Delete via form POST
        del_status, _, del_html = self._run_request(
            "POST", "/announcements/1/delete"
        )
        self.assertEqual(del_status, 200)
        self.assertIn("başarıyla silindi", del_html)

        # Step 8: Verify list is empty again
        final_list_status, _, final_list_html = self._run_request(
            "GET", "/announcements", headers={"accept": "text/html"}
        )
        self.assertEqual(final_list_status, 200)
        self.assertIn("No announcements found", final_list_html)

        final_detail_status, _, _ = self._run_request(
            "GET", "/announcements/1", headers={"accept": "text/html"}
        )
        self.assertEqual(final_detail_status, 404)


if __name__ == "__main__":
    unittest.main()
