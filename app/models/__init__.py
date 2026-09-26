"""Database models package.

Contains SQLAlchemy ORM models representing the database tables.
In subsequent stages, Alumni, Department, Education, and Career models will be registered here.
"""

from app.core.database import Base

__all__ = ["Base"]
