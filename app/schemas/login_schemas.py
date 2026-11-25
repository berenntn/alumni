"""Pydantic schemas for User Login authentication requests and responses."""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserLoginRequest(BaseModel):
    """Request schema for alumni user login."""

    email: str = Field(..., description="Kullanıcı e-posta adresi", examples=["ayse@alumni.istanbul.edu.tr"])
    password: str = Field(..., min_length=1, description="Kullanıcı şifresi", examples=["GizliSifre123"])

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower() if isinstance(v, str) else ""
        if not cleaned or not EMAIL_REGEX.match(cleaned):
            raise ValueError("Geçerli bir e-posta adresi giriniz.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Şifre alanı boş bırakılamaz.")
        return v


class UserLoginResponseData(BaseModel):
    """User data returned in login response."""

    id: int
    name: str
    email: str
    department: str
    graduation_year: int
    role: str = "alumnus"


class UserLoginApiResponse(BaseModel):
    """API response model for successful user authentication."""

    status: str = "success"
    message: str = "Giriş başarılı."
    data: Optional[UserLoginResponseData] = None
    redirect_url: str = "/dashboard"
