"""HTTP Request Logging Middleware for Alumni Tracking System.

Logs every incoming request with:
- Timestamp (UTC)
- HTTP Method
- URL Path
- Response HTTP Status Code
- Execution duration in milliseconds
"""

import logging
import time
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs timestamp, method, path, response status, and duration (ms) for all HTTP requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            f"[{timestamp}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration_ms:.2f}ms"
        )

        return response
