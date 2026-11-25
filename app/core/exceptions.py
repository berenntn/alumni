"""Global exception handlers for Alumni Tracking System.

Provides:
- Custom 404 handler returning HTML for browser requests and JSON for API requests.
- Safe global 5xx error handling that logs full tracebacks to logs/error.log
  without exposing sensitive system details to clients.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logger = logging.getLogger("app.error")
templates = Jinja2Templates(directory="app/templates")


def _is_api_request(request: Request) -> bool:
    """Determines whether a request is targeted at the API or a web browser.

    API requests:
    - Path starts with /api/
    - Accept header explicitly prioritizes application/json or lacks text/html
    """
    path = request.url.path
    if path.startswith("/api/"):
        return True

    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return False

    return True


async def not_found_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles 404 Not Found errors for both web and API routes."""
    if _is_api_request(request):
        detail_msg = exc.detail if exc.detail and exc.detail != "Not Found" else "Resource not found"
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": detail_msg,
                "detail": exc.detail or "Not Found",
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={
            "detail": exc.detail if exc.detail and exc.detail != "Not Found" else "Aradığınız sayfa bulunamadı.",
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
        },
        status_code=404,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles Starlette and FastAPI HTTPExceptions."""
    if exc.status_code == 404:
        return await not_found_exception_handler(request, exc)

    if exc.status_code == 403 and not _is_api_request(request):
        return templates.TemplateResponse(
            request=request,
            name="403.html",
            context={
                "detail": exc.detail if exc.detail else "Bu sayfaya erişim yetkiniz bulunmamaktadır.",
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "user": getattr(request.state, "user", None),
            },
            status_code=403,
        )

    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} Error on {request.method} {request.url.path}: {exc.detail}",
            exc_info=True,
        )
        if _is_api_request(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "status": "error",
                    "message": "Internal Server Error",
                    "detail": "An unexpected error occurred. Please contact system administrator if this persists.",
                },
            )
        return templates.TemplateResponse(
            request=request,
            name="500.html",
            context={
                "app_name": settings.APP_NAME,
                "app_title_tr": settings.APP_TITLE_TR,
                "app_description": settings.APP_DESCRIPTION,
                "error_message": "Sunucuda beklenmeyen bir hata oluştu.",
            },
            status_code=exc.status_code,
        )

    # For 4xx client errors (400, 401, 403, 422, etc.)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "detail": exc.detail,
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Catches all unexpected 5xx errors, logs full traceback, and returns safe responses."""
    logger.error(
        f"Unhandled server error during {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )

    if _is_api_request(request):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal Server Error",
                "detail": "An unexpected error occurred. Please contact system administrator if this persists.",
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="500.html",
        context={
            "app_name": settings.APP_NAME,
            "app_title_tr": settings.APP_TITLE_TR,
            "app_description": settings.APP_DESCRIPTION,
            "error_message": "Sunucuda beklenmeyen bir hata meydana geldi.",
        },
        status_code=500,
    )


def register_exception_handlers(app: FastAPI):
    """Registers exception handlers with the FastAPI application instance."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
