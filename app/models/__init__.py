"""Database models package.

Contains SQLAlchemy ORM models representing the database tables.
In subsequent stages, Alumni, Department, Education, and Career models will be registered here.
"""

from app.core.database import Base
from app.models.announcement import Announcement, AnnouncementDB
from app.models.user import User
from app.models.job_posting import JobPostingDB

__all__ = ["Announcement", "AnnouncementDB", "Base", "User", "JobPostingDB"]
