"""Tests for application API routes."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.main import app
from app.models.user_db import UserDB
from app.services.session_service import SessionService, clear_sessions


class TestApplicationRoutes(unittest.TestCase):

    def setUp(self):
        with get_db_session() as db:
            db.query(UserDB).filter(UserDB.email == "admin@alumni.test").delete()
            admin = UserDB(
                id=1,
                name="Admin Test",
                email="admin@alumni.test",
                department="Bilgisayar",
                graduation_year=2020,
                role="admin",
            )
            db.merge(admin)
            db.flush()
        token = SessionService.create_session(admin)
        self.client = TestClient(app)
        self.client.headers["Authorization"] = f"Bearer {token}"

    def tearDown(self):
        clear_sessions()
        with get_db_session() as db:
            db.query(UserDB).filter(UserDB.email == "admin@alumni.test").delete()

    def test_application_routes_registered(self):
        routes = {
            (route.path, method)
            for route in app.routes
            for method in getattr(route, "methods", [])
        }

        expected = {
            ("/api/applications", "GET"),
            ("/api/applications", "POST"),
            ("/api/applications/{application_id}", "GET"),
            ("/api/applications/{application_id}", "PATCH"),
            ("/api/applications/{application_id}", "DELETE"),
            ("/api/users/{user_id}/applications", "GET"),
            ("/api/job-postings/{job_posting_id}/applications", "GET"),
        }

        self.assertTrue(expected.issubset(routes))

    def test_list_applications_empty(self):
        with patch("app.api.application_routes.get_db_session") as mock_db:
            session = mock_db.return_value.__enter__.return_value
            session.execute.return_value.scalars.return_value.all.return_value = []

            response = self.client.get("/api/applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_user_applications_empty(self):
        with patch("app.api.application_nested_routes.get_db_session") as mock_db:
            session = mock_db.return_value.__enter__.return_value
            session.execute.return_value.scalars.return_value.all.return_value = []

            response = self.client.get("/api/users/1/applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_job_posting_applications_empty(self):
        with patch("app.api.application_nested_routes.get_db_session") as mock_db:
            session = mock_db.return_value.__enter__.return_value
            session.execute.return_value.scalars.return_value.all.return_value = []

            response = self.client.get("/api/job-postings/1/applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_invalid_user_id(self):
        response = self.client.get("/api/users/0/applications")
        self.assertEqual(response.status_code, 422)

    def test_invalid_application_payload(self):
        response = self.client.post(
            "/api/applications",
            json={"user_id": 0, "job_posting_id": 1},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
