"""Pydantic schemas for User Registration requests and responses."""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# Standard RFC-compliant email regular expression
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Request schema for alumni user registration."""

    name: str = Field(..., min_length=1, description="Kullanıcı adı ve soyadı", examples=["Ayşe Yılmaz"])
    email: str = Field(..., description="Geçerli e-posta adresi", examples=["ayse@alumni.istanbul.edu.tr"])
    department: str = Field(..., min_length=1, description="Mezun olunan bölüm", examples=["Bilgisayar Mühendisliği"])
    graduation_year: int = Field(..., ge=1900, le=2100, description="Mezuniyet yılı", examples=[2024])
    password: str = Field(..., min_length=8, description="En az 8 karakterli şifre", examples=["GizliSifre123"])
    confirm_password: str = Field(..., min_length=8, description="Şifre doğrulama", examples=["GizliSifre123"])

    @field_validator("name", "department")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        cleaned = v.strip() if isinstance(v, str) else ""
        if not cleaned:
            raise ValueError("Alan boş bırakılamaz.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower() if isinstance(v, str) else ""
        if not cleaned or not EMAIL_REGEX.match(cleaned):
            raise ValueError("Geçerli bir e-posta adresi giriniz.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır.")
        return v

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Şifreler birbiriyle eşleşmiyor.")
        return self


class UserRegisterResponseData(BaseModel):
    """Safe user data returned upon successful registration (passwords omitted)."""

    id: int
    name: str
    email: str
    department: str
    graduation_year: int
    role: str = "alumnus"


class UserRegisterApiResponse(BaseModel):
    """API response model for successful user registration."""

    status: str = "success"
    message: str = "Kullanıcı kaydı başarıyla oluşturuldu."
    data: Optional[UserRegisterResponseData] = None
