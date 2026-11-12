"""Tests for HTTP request logging middleware, custom 404 handling, and safe 5xx exception handling."""

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logging_config import ERROR_LOG_PATH
import app.api.test_routes as test_routes_module
from app.main import app


class TestMiddlewareAndExceptions(unittest.TestCase):
    """Test suite verifying middleware logging, 404 HTML/JSON differentiation, and safe 5xx handling."""

    def setUp(self):
        # Use raise_server_exceptions=False so TestClient allows FastAPI exception handlers to process 500 errors
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        # Guarantee settings.DEBUG is restored and test_routes is reloaded
        if not settings.DEBUG:
            settings.DEBUG = True
            importlib.reload(test_routes_module)

    # -------------------------------------------------------------------------
    # 1. HTTP Request Logging Middleware Tests
    # -------------------------------------------------------------------------

    def test_middleware_logs_request_details(self):
        """Middleware should log timestamp, method, path, status, and duration in ms."""
        with patch("app.core.middleware.logger.info") as mock_logger:
            response = self.client.get("/hello")
            self.assertEqual(response.status_code, 200)

            self.assertTrue(mock_logger.called)
            log_message = mock_logger.call_args[0][0]

            # Verify presence of required fields
            self.assertIn("GET", log_message)
            self.assertIn("/hello", log_message)
            self.assertIn("Status: 200", log_message)
            self.assertIn("Duration:", log_message)
            self.assertIn("ms", log_message)
            self.assertIn("UTC", log_message)

    # -------------------------------------------------------------------------
    # 2. Custom 404 Handling Tests (Browser HTML vs API JSON)
    # -------------------------------------------------------------------------

    def test_browser_404_returns_html(self):
        """Browser request to non-existent route with text/html should return custom 404 HTML page."""
        response = self.client.get(
            "/nonexistent-page-url-xyz",
            headers={"Accept": "text/html,application/xhtml+xml"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("404", response.text)
        self.assertIn("Sayfa Bulunamadı", response.text)
        self.assertIn("Ana Sayfaya Dön", response.text)

    def test_api_404_returns_json(self):
        """API request to non-existent route under /api/ should return structured JSON 404."""
        response = self.client.get("/api/nonexistent-route-endpoint")
        self.assertEqual(response.status_code, 404)
        self.assertIn("application/json", response.headers.get("content-type", ""))
        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("detail", data)

    def test_api_404_with_explicit_accept_json(self):
        """Request asking for JSON to non-existent route should return JSON 404."""
        response = self.client.get(
            "/random-missing-path",
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("application/json", response.headers.get("content-type", ""))
        data = response.json()
        self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # 3. Safe 5xx Exception Handling & error.log Tests
    # -------------------------------------------------------------------------

    def test_safe_500_response_for_api_route(self):
        """Unexpected 500 error on API route must return clean JSON without exposing sensitive details."""
        response = self.client.get("/api/test/error-500")
        self.assertEqual(response.status_code, 500)
        self.assertIn("application/json", response.headers.get("content-type", ""))

        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("message"), "Internal Server Error")

        # Crucial security check: sensitive traceback / internal exception message must NOT be exposed
        self.assertNotIn("RuntimeError", response.text)
        self.assertNotIn("Simulated unhandled", response.text)
        self.assertNotIn("Traceback", response.text)

    def test_500_error_is_written_to_error_log_file(self):
        """Server-side exception details and traceback must be recorded in logs/error.log."""
        # Trigger the 500 error
        response = self.client.get("/api/test/error-500")
        self.assertEqual(response.status_code, 500)

        # Check error.log file exists
        self.assertTrue(ERROR_LOG_PATH.exists(), f"Log file at {ERROR_LOG_PATH} should exist.")

        # Read error.log content
        with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
            log_content = f.read()

        # Check full traceback and error details are logged server-side
        self.assertIn("Simulated unhandled internal server error for testing", log_content)
        self.assertIn("RuntimeError", log_content)
        self.assertIn("ERROR", log_content)

    def test_safe_500_response_for_browser_route(self):
        """Unexpected 500 error for browser request should return safe 500 HTML page."""
        response = self.client.get(
            "/api/test/error-500",
            headers={"Accept": "text/html"},
        )
        self.assertEqual(response.status_code, 500)

    # -------------------------------------------------------------------------
    # 4. Conditional Registration of /api/test/error-500 by settings.DEBUG
    # -------------------------------------------------------------------------

    def test_error_500_endpoint_available_when_debug_is_true(self):
        """When settings.DEBUG is True, /api/test/error-500 must be registered and return HTTP 500."""
        settings.DEBUG = True
        importlib.reload(test_routes_module)

        route_paths = [route.path for route in test_routes_module.test_router.routes]
        self.assertIn("/api/test/error-500", route_paths)

        # Verify endpoint returns 500
        res = self.client.get("/api/test/error-500")
        self.assertEqual(res.status_code, 500)

    def test_error_500_endpoint_unavailable_when_debug_is_false(self):
        """When settings.DEBUG is False, /api/test/error-500 must NOT be registered and return HTTP 404."""
        settings.DEBUG = False
        importlib.reload(test_routes_module)

        route_paths = [route.path for route in test_routes_module.test_router.routes]
        self.assertNotIn(
            "/api/test/error-500",
            route_paths,
            "Endpoint /api/test/error-500 must not be registered when DEBUG is False.",
        )

        # Build app instance with the DEBUG=False router to test HTTP response
        test_app = FastAPI()
        from app.core.exceptions import register_exception_handlers
        register_exception_handlers(test_app)
        test_app.include_router(test_routes_module.test_router)
        client = TestClient(test_app)

        # Endpoint returns 404 Not Found
        response = client.get("/api/test/error-500")
        self.assertEqual(response.status_code, 404)

        # Calculator and greeting routes must remain preserved and functional
        hello_res = client.get("/hello")
        self.assertEqual(hello_res.status_code, 200)

        sum_res = client.get("/sum/10/20")
        self.assertEqual(sum_res.status_code, 200)
        self.assertEqual(sum_res.json()["result"], 30)


if __name__ == "__main__":
    unittest.main()
