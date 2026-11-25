import os
import sys
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Project Information
    APP_NAME: str = "Alumni Tracking System"
    APP_TITLE_TR: str = "İstanbul Üniversitesi Mezun Takip Sistemi"
    APP_DESCRIPTION: str = (
        "İstanbul Üniversitesi Mezun Takip Sistemi - Web Programlama dersi "
        "kapsamında geliştirilen, mezunlar ve üniversite arasındaki bağı güçlendiren modern web platformu."
    )
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & Session Configuration
    SECRET_KEY: str = "alumni-tracking-system-dev-secret-key-change-in-production-2026"
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_MAX_AGE: int = 604800  # 7 days in seconds
    SESSION_COOKIE_SECURE: Optional[bool] = None

    # PostgreSQL Database Configuration
    POSTGRES_USER: str = "alumni_user"
    POSTGRES_PASSWORD: str = "alumni_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "alumni_db"
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Returns True if the application environment is configured as production."""
        return (self.APP_ENV or "").lower().strip() in ("production", "prod")

    @property
    def session_cookie_secure(self) -> bool:
        """Returns True if session cookies must strictly be sent over HTTPS.

        Defaults to True in production environments, and False in development/test
        unless explicitly overridden by the SESSION_COOKIE_SECURE environment variable.
        """
        if self.SESSION_COOKIE_SECURE is not None:
            return self.SESSION_COOKIE_SECURE
        return self.is_production

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforces security requirements in production.

        In production:
        - SECRET_KEY must be explicitly set from an environment variable.
        - Must not use any hardcoded, development, or predictable fallback values.
        - Must be at least 32 characters in length for cryptographic strength.
        """
        if self.is_production:
            insecure_fallbacks = {
                "alumni-tracking-system-dev-secret-key-change-in-production-2026",
                "alumni-tracking-system-super-secret-key-2026",
                "secret",
                "changeme",
                "password",
                "12345678",
                "",
            }
            key = (self.SECRET_KEY or "").strip()
            if not key or key in insecure_fallbacks:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production, SECRET_KEY must be set "
                    "via an environment variable and cannot use a hardcoded or predictable fallback. "
                    "Set SECRET_KEY=<strong_random_secret_at_least_32_characters>."
                )
            if len(key) < 32:
                raise ValueError(
                    f"CRITICAL SECURITY CONFIGURATION ERROR: In production, SECRET_KEY must be at least "
                    f"32 characters long for cryptographic security (got {len(key)} characters)."
                )
        return self

    def get_database_url(self) -> str:
        """Returns the configured database URL or generates one from Postgres params."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if (
            self.APP_ENV == "test"
            or os.environ.get("TESTING", "").lower() in ("true", "1")
            or "unittest" in sys.modules
        ):
            return "sqlite:///:memory:"
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
