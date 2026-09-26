import os
from typing import Optional
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

    def get_database_url(self) -> str:
        """Returns the configured database URL or generates one from Postgres params."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
