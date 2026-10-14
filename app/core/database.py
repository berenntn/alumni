"""Database setup and session management using SQLAlchemy."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
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
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool if ":memory:" in db_url else None
            if poolclass:
                engine = create_engine(db_url, connect_args=connect_args, poolclass=poolclass)
            else:
                engine = create_engine(db_url, connect_args=connect_args)
        else:
            engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def init_db():
    """Initializes database tables defined in SQLAlchemy Base metadata."""
    eng = get_engine()
    # Import models package to register all models with Base.metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=eng)


def reset_engine():
    """Disposes existing engine and resets connection state (for test isolation)."""
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    engine = None
    SessionLocal = None


@contextmanager
def get_db_session():
    """Context manager providing a transactional database session."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator:
    """Dependency that yields a database session for request lifecycles."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
