"""SQLAlchemy model for alumni users."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserDB(Base):
    """Database model representing an alumni user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    department = Column(String(255), nullable=False)
    graduation_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    announcements = relationship(
        "AnnouncementDB",
        back_populates="author",
    )
