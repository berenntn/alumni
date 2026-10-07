"""User model representing an alumni/user entity without database dependencies."""

from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """User entity model representing basic alumni information.

    Attributes:
        id: Unique identifier for the user (optional upon creation, assigned by service).
        name: Full name of the alumni/user.
        email: Email address of the user.
        department: Department graduated from or enrolled in.
        graduation_year: Year of graduation.
    """

    id: Optional[int] = Field(default=None, description="Benzersiz kullanıcı kimliği")
    name: str = Field(..., description="Kullanıcı / Mezun adı soyadı", min_length=1)
    email: str = Field(..., description="Kullanıcı e-posta adresi")
    department: str = Field(..., description="Mezun olunan veya kayıtlı olunan bölüm")
    graduation_year: int = Field(..., description="Mezuniyet yılı", ge=1900, le=2100)
