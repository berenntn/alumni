"""SQLAlchemy and Pydantic models for alumni job postings."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class JobPostingDB(Base):
    """Database model representing a job posting."""

    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class JobPosting(BaseModel):
    """Job posting domain and validation model.

    Validation rules:
    - title: required, max 120 characters
    - company_name: required
    - location / city: optional
    - description: optional
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, description="Benzersiz iş ilanı kimliği")
    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="İş ilanı başlığı (Zorunlu, Maksimum 120 karakter)",
    )
    company_name: str = Field(
        ...,
        min_length=1,
        description="Şirket / Kurum adı (Zorunlu)",
    )
    location: Optional[str] = Field(
        default=None,
        description="Şehir veya lokasyon bilgisi (Opsiyonel)",
    )
    description: Optional[str] = Field(
        default="",
        description="İş tanımı ve detaylar (Opsiyonel)",
    )
    employment_type: Optional[str] = Field(
        default=None,
        description="Çalışma türü (Opsiyonel, örn: Tam Zamanlı, Staj, Hibrit)",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Oluşturulma tarihi",
    )
