"""Pydantic schemas for Job Posting API requests, responses, and validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class JobPostingCreateRequest(BaseModel):
    """Request schema for creating a new job posting.

    Validation rules:
    - title: required, max 120 characters
    - company_name: required
    - location / city: optional
    - description: optional
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="İş ilanı başlığı (Zorunlu, Maksimum 120 karakter)",
        examples=["Junior Python Developer"],
    )
    company_name: str = Field(
        ...,
        min_length=1,
        description="Şirket / Kurum adı (Zorunlu)",
        examples=["TechNova"],
    )
    location: Optional[str] = Field(
        default=None,
        description="Şehir veya lokasyon (Opsiyonel)",
        examples=["Istanbul"],
    )
    city: Optional[str] = Field(
        default=None,
        description="Şehir alternatifi (Opsiyonel)",
        examples=["Istanbul"],
    )
    description: Optional[str] = Field(
        default="",
        description="İş tanımı ve sorumluluklar (Opsiyonel)",
        examples=["Develop backend services using Python and FastAPI."],
    )
    employment_type: Optional[str] = Field(
        default=None,
        description="Çalışma biçimi (Opsiyonel: Full-time, Internship, Hybrid, Remote)",
        examples=["Full-time"],
    )

    @model_validator(mode="after")
    def resolve_location(self) -> "JobPostingCreateRequest":
        """Resolves city alias to location if location is not explicitly provided."""
        if not self.location and self.city:
            self.location = self.city
        return self


class JobPostingUpdateRequest(BaseModel):
    """Request schema for fully updating (PUT) an existing job posting."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="İş ilanı başlığı (Zorunlu, Maksimum 120 karakter)",
        examples=["Senior Python Developer"],
    )
    company_name: str = Field(
        ...,
        min_length=1,
        description="Şirket / Kurum adı (Zorunlu)",
        examples=["TechNova Corp"],
    )
    location: Optional[str] = Field(
        default=None,
        description="Şehir veya lokasyon (Opsiyonel)",
        examples=["Istanbul / Remote"],
    )
    city: Optional[str] = Field(
        default=None,
        description="Şehir alternatifi (Opsiyonel)",
        examples=["Istanbul"],
    )
    description: Optional[str] = Field(
        default="",
        description="İş tanımı ve sorumluluklar (Opsiyonel)",
        examples=["Lead the backend architecture team."],
    )
    employment_type: Optional[str] = Field(
        default=None,
        description="Çalışma biçimi (Opsiyonel)",
        examples=["Remote"],
    )

    @model_validator(mode="after")
    def resolve_location(self) -> "JobPostingUpdateRequest":
        """Resolves city alias to location if location is not explicitly provided."""
        if not self.location and self.city:
            self.location = self.city
        return self


class JobPostingPatchRequest(BaseModel):
    """Request schema for partially updating (PATCH) an existing job posting."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120,
        description="Güncellenecek başlık (Opsiyonel, Maksimum 120 karakter)",
        examples=["Mid-level Backend Developer"],
    )
    company_name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Güncellenecek şirket adı (Opsiyonel)",
        examples=["TechNova Innovations"],
    )
    location: Optional[str] = Field(
        default=None,
        description="Güncellenecek lokasyon (Opsiyonel)",
        examples=["Ankara"],
    )
    city: Optional[str] = Field(
        default=None,
        description="Güncellenecek şehir (Opsiyonel)",
        examples=["Ankara"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Güncellenecek iş tanımı (Opsiyonel)",
        examples=["Updated job requirements."],
    )
    employment_type: Optional[str] = Field(
        default=None,
        description="Güncellenecek çalışma biçimi (Opsiyonel)",
        examples=["Hybrid"],
    )

    @model_validator(mode="after")
    def resolve_location(self) -> "JobPostingPatchRequest":
        """Resolves city alias to location if location is not explicitly provided."""
        if not self.location and self.city:
            self.location = self.city
        return self


class JobPostingResponseData(BaseModel):
    """Schema representing serialized job posting data in API responses."""

    id: Optional[int] = Field(default=None, description="Benzersiz iş ilanı ID'si", examples=[1])
    title: str = Field(..., description="İş ilanı başlığı", examples=["Junior Python Developer"])
    company_name: str = Field(..., description="Şirket adı", examples=["TechNova"])
    location: Optional[str] = Field(default=None, description="Lokasyon / Şehir", examples=["Istanbul"])
    description: Optional[str] = Field(default="", description="İş tanımı", examples=["Develop backend services..."])
    employment_type: Optional[str] = Field(default=None, description="Çalışma biçimi", examples=["Full-time"])
    created_at: Optional[datetime] = Field(default=None, description="Oluşturulma tarihi")


class JobPostingApiResponse(BaseModel):
    """Standard API envelope response for single job posting operations."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["Job posting created successfully"])
    data: Optional[JobPostingResponseData] = Field(default=None, description="İş ilanı verisi")


class JobPostingListApiResponse(BaseModel):
    """Standard API envelope response for job posting collection queries."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["Retrieved 5 job postings"])
    data: List[JobPostingResponseData] = Field(default_factory=list, description="İş ilanları listesi")
    count: int = Field(..., description="Toplam iş ilanı sayısı", examples=[5])


class JobPostingDeleteApiResponse(BaseModel):
    """Standard API envelope response for job posting deletion."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: str = Field(..., description="Silme sonuç bildirimi", examples=["Job posting deleted successfully"])
