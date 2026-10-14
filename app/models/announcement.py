"""Announcement models representing notice entities for PostgreSQL and Pydantic validation."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AnnouncementDB(Base):
    """SQLAlchemy ORM model representing the announcements table in PostgreSQL."""

    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(Integer, nullable=True)


class Announcement(BaseModel):
    """Announcement entity model representing announcements and notices in the system.

    Attributes:
        id: Unique identifier for the announcement (optional upon creation).
        title: Title/subject of the announcement (required, min length 1).
        content: Detailed message content of the announcement (required, min length 1).
        created_by: Identifier of the user who created the announcement (optional).
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, description="Benzersiz duyuru kimliği")
    title: str = Field(..., description="Duyuru başlığı", min_length=1)
    content: str = Field(..., description="Duyuru içeriği / metni", min_length=1)
    created_by: Optional[int] = Field(default=None, description="Duyuruyu oluşturan kullanıcı kimliği")
