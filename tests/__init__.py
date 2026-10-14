"""Test package for alumni tracking system."""

import os

# Configure isolated in-memory SQLite database for unit tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TESTING", "true")

from app.core.config import settings
if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("postgresql://alumni_user:alumni_password@localhost"):
    settings.DATABASE_URL = os.environ["DATABASE_URL"]
settings.APP_ENV = "test"

from app.core.database import init_db
init_db()
