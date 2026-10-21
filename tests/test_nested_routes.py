import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app


class TestNestedRoutes(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_nested_route_is_registered(self):
        paths = [route.path for route in app.routes]
        self.assertIn(
            "/api/users/{user_id}/announcements",
            paths,
        )

    def test_nested_route_returns_empty_list(self):
        with patch("app.api.nested_routes.get_db_session") as mock_db:
            session = mock_db.return_value.__enter__.return_value
            session.execute.return_value.scalars.return_value.all.return_value = []

            response = self.client.get("/api/users/1/announcements")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_invalid_user_id(self):
        response = self.client.get("/api/users/0/announcements")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
