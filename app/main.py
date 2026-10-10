"""Main FastAPI application entrypoint."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.web_routes import web_router
from app.api.test_routes import test_router
from app.api.health_routes import router as health_router
from app.api.user_routes import router as user_router
from app.api.announcement_routes import router as announcement_router
from app.core.config import settings

# Base directory for resolving static and template directories
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=f"{settings.APP_NAME} | {settings.APP_TITLE_TR}",
    description=(
        "İstanbul Üniversitesi Web Programlama Dersi - Mezun Takip Sistemi REST API & Web Portalı.\n\n"
        "Bu aşamada katmanlı mimari temeli, HTML/CSS arayüzü ve test uç noktaları sunulmaktadır."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Web Pages", "description": "Kullanıcı arayüzü ve web rotaları (UserController & AnnouncementController)"},
        {"name": "Users", "description": "Kullanıcı REST API CRUD uç noktaları (ApiUserController)"},
        {"name": "Announcements", "description": "Duyuru REST API CRUD uç noktaları (ApiAnnouncementController)"},
        {"name": "Health", "description": "Sistem sağlık kontrolü uç noktaları"},
        {"name": "Test Endpoints", "description": "Temel test ve hesaplama uç noktaları"},
    ],
)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
