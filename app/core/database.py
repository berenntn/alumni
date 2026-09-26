"""Database setup and session management using SQLAlchemy."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

Base = declarative_base()

# Lazy/resilient engine creation: connection is established upon checkout
engine = None
SessionLocal = None

def get_engine():
    """Lazily initialize the SQLAlchemy engine."""
    global engine, SessionLocal
    if engine is None:
        db_url = settings.get_database_url()
        # Fallback handling for SQLite if testing without Postgres locally
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def get_db() -> Generator:
    """Dependency that yields a database session for request lifecycles."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
