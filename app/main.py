"""Main FastAPI application entrypoint for Alumni Tracking System."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Initialize logging configuration before other imports
import app.core.logging_config  # noqa: F401

from app.api.web_routes import web_router
from app.api.test_routes import test_router
from app.api.health_routes import router as health_router
from app.api.user_routes import router as user_router
from app.api.announcement_routes import router as announcement_router
from app.api.nested_routes import router as nested_router
from app.api.application_routes import router as application_router
from app.api.application_nested_routes import router as application_nested_router
from app.api.job_posting_routes import router as job_posting_router
from app.api.job_web_routes import router as job_web_router

from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import RequestLoggingMiddleware
from app.core.csrf_middleware import CSRFProtectionMiddleware
from app.core.exceptions import register_exception_handlers

# Base directory for resolving static and template directories
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that initializes database tables on startup."""
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} | {settings.APP_TITLE_TR}",
    description=(
        "İstanbul Üniversitesi Web Programlama Dersi - Mezun Takip Sistemi REST API & Web Portalı.\n\n"
        "Katmanlı MVC mimarisi, veri doğrulama, HTTP middleware loglama, güvenli hata yönetimi "
        "ve mezun/duyuru/iş ilanı/başvuru modülleri sunulmaktadır."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Web Pages", "description": "Kullanıcı arayüzü ve web rotaları (UserController & AnnouncementController)"},
        {"name": "Users", "description": "Kullanıcı REST API CRUD uç noktaları (ApiUserController)"},
        {"name": "Announcements", "description": "Duyuru REST API CRUD uç noktaları (ApiAnnouncementController)"},
        {"name": "Job Postings", "description": "İş İlanları REST API CRUD uç noktaları"},
        {"name": "Applications", "description": "İş Başvuruları REST API uç noktaları"},
        {"name": "Health", "description": "Sistem sağlık kontrolü uç noktaları"},
        {"name": "Test Endpoints", "description": "Temel test, hesaplama ve hata simülasyonu uç noktaları"},
    ],
)

# Register HTTP request logging and CSRF protection middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CSRFProtectionMiddleware)

# Register custom exception handlers (Custom 404 HTML/JSON & Safe 5xx handler)
register_exception_handlers(app)

# Mount static files (CSS, JS, images)
static_path = BASE_DIR / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Register routers
app.include_router(web_router)
app.include_router(test_router)
app.include_router(health_router)
app.include_router(user_router)
app.include_router(announcement_router)
app.include_router(nested_router)
app.include_router(job_posting_router)
app.include_router(application_router)
app.include_router(application_nested_router)
app.include_router(job_web_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
