"""Pydantic schemas for Announcement API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AnnouncementCreateRequest(BaseModel):
    """Request schema for creating a new announcement."""

    title: str = Field(..., description="Duyuru başlığı", min_length=1, examples=["Mezunlar Buluşması 2026"])
    content: str = Field(..., description="Duyuru metni / içeriği", min_length=1, examples=["15 Mayıs'ta Rektörlük bahçesinde buluşuyoruz."])
    created_by: Optional[int] = Field(default=None, description="Duyuruyu oluşturan kullanıcı kimliği", examples=[1])


class AnnouncementUpdateRequest(BaseModel):
    """Request schema for full update (PUT) of an announcement."""

    title: str = Field(..., description="Duyuru başlığı", min_length=1, examples=["Mezunlar Buluşması 2026"])
    content: str = Field(..., description="Duyuru metni / içeriği", min_length=1, examples=["15 Mayıs'ta Rektörlük bahçesinde buluşuyoruz."])
    created_by: Optional[int] = Field(default=None, description="Duyuruyu oluşturan kullanıcı kimliği", examples=[1])


class AnnouncementPatchRequest(BaseModel):
    """Request schema for partial update (PATCH) of an announcement."""

    title: Optional[str] = Field(default=None, description="Güncellenecek duyuru başlığı", min_length=1, examples=["Güncel Başlık"])
    content: Optional[str] = Field(default=None, description="Güncellenecek duyuru metni", min_length=1, examples=["Güncel İçerik"])
    created_by: Optional[int] = Field(default=None, description="Güncellenecek oluşturan kimliği", examples=[2])


class AnnouncementResponseData(BaseModel):
    """Schema representing announcement data in API responses."""

    id: Optional[int] = Field(default=None, description="Benzersiz duyuru ID'si", examples=[1])
    title: str = Field(..., description="Duyuru başlığı", examples=["Mezunlar Buluşması 2026"])
    content: str = Field(..., description="Duyuru içeriği", examples=["15 Mayıs'ta Rektörlük bahçesinde buluşuyoruz."])
    created_by: Optional[int] = Field(default=None, description="Duyuruyu oluşturan kullanıcı ID'si", examples=[1])


class AnnouncementApiResponse(BaseModel):
    """Standard API response for single-announcement operations."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["Announcement created successfully"])
    data: Optional[AnnouncementResponseData] = Field(default=None, description="Duyuru verisi")


class AnnouncementListApiResponse(BaseModel):
    """Standard API response for announcement collection queries."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["Retrieved 2 announcements"])
    data: List[AnnouncementResponseData] = Field(default_factory=list, description="Duyuru listesi")
    count: int = Field(..., description="Toplam duyuru sayısı", examples=[2])


class AnnouncementDeleteApiResponse(BaseModel):
    """Standard API response for announcement deletion."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: str = Field(..., description="Silme işlem sonucu", examples=["Announcement 1 deleted successfully"])
