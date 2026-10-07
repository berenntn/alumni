"""Pydantic schemas for User API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user."""

    name: str = Field(..., description="Kullanıcı / Mezun tam adı", min_length=1, examples=["Berkay Tuna"])
    email: str = Field(..., description="Kullanıcı e-posta adresi", examples=["berkay@alumni.istanbul.edu.tr"])
    department: str = Field(..., description="Mezun olunan veya kayıtlı bölüm", examples=["Bilgisayar Mühendisliği"])
    graduation_year: int = Field(..., description="Mezuniyet yılı", ge=1900, le=2100, examples=[2024])


class UserUpdateRequest(BaseModel):
    """Request schema for full update (PUT) of a user."""

    name: str = Field(..., description="Kullanıcı / Mezun tam adı", min_length=1, examples=["Berkay Tuna"])
    email: str = Field(..., description="Kullanıcı e-posta adresi", examples=["berkay.tuna@alumni.istanbul.edu.tr"])
    department: str = Field(..., description="Mezun olunan bölüm", examples=["Yazılım Mühendisliği"])
    graduation_year: int = Field(..., description="Mezuniyet yılı", ge=1900, le=2100, examples=[2024])


class UserPatchRequest(BaseModel):
    """Request schema for partial update (PATCH) of a user."""

    name: Optional[str] = Field(default=None, description="Güncellenecek tam ad", min_length=1, examples=["Berkay Tuna"])
    email: Optional[str] = Field(default=None, description="Güncellenecek e-posta", examples=["berkay.yeni@alumni.istanbul.edu.tr"])
    department: Optional[str] = Field(default=None, description="Güncellenecek bölüm", examples=["Bilgisayar Mühendisliği"])
    graduation_year: Optional[int] = Field(default=None, description="Güncellenecek mezuniyet yılı", ge=1900, le=2100, examples=[2025])


class UserResponseData(BaseModel):
    """Schema representing user data in API responses."""

    id: Optional[int] = Field(default=None, description="Benzersiz kullanıcı ID'si", examples=[1])
    name: str = Field(..., description="Kullanıcı adı soyadı", examples=["Berkay Tuna"])
    email: str = Field(..., description="E-posta adresi", examples=["berkay@alumni.istanbul.edu.tr"])
    department: str = Field(..., description="Bölüm", examples=["Bilgisayar Mühendisliği"])
    graduation_year: int = Field(..., description="Mezuniyet yılı", examples=[2024])


class UserApiResponse(BaseModel):
    """Standard API response for single-user operations."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["User created successfully"])
    data: Optional[UserResponseData] = Field(default=None, description="Kullanıcı verisi")


class UserListApiResponse(BaseModel):
    """Standard API response for user collection queries."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: Optional[str] = Field(default=None, description="Açıklama mesajı", examples=["Retrieved 2 users"])
    data: List[UserResponseData] = Field(default_factory=list, description="Kullanıcı listesi")
    count: int = Field(..., description="Toplam kullanıcı sayısı", examples=[2])


class UserDeleteApiResponse(BaseModel):
    """Standard API response for user deletion."""

    status: str = Field(..., description="İşlem durumu ('success' veya 'error')", examples=["success"])
    message: str = Field(..., description="Silme işlem sonucu", examples=["User 1 deleted successfully"])
