"""Announcement model representing a notice or announcement entity without database dependencies."""

from typing import Optional
from pydantic import BaseModel, Field


class Announcement(BaseModel):
    """Announcement entity model representing announcements and notices in the system.

    Attributes:
        id: Unique identifier for the announcement (optional upon creation).
        title: Title/subject of the announcement (required, min length 1).
        content: Detailed message content of the announcement (required, min length 1).
        created_by: Identifier of the user who created the announcement (optional).
    """

    id: Optional[int] = Field(default=None, description="Benzersiz duyuru kimliği")
    title: str = Field(..., description="Duyuru başlığı", min_length=1)
    content: str = Field(..., description="Duyuru içeriği / metni", min_length=1)
    created_by: Optional[int] = Field(default=None, description="Duyuruyu oluşturan kullanıcı kimliği")
