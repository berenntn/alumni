"""Pydantic schemas package for data validation and serialization."""

from app.schemas.announcement_schemas import (
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
    AnnouncementPatchRequest,
    AnnouncementResponseData,
    AnnouncementApiResponse,
    AnnouncementListApiResponse,
    AnnouncementDeleteApiResponse,
)
from app.schemas.job_posting_schemas import (
    JobPostingCreateRequest,
    JobPostingUpdateRequest,
    JobPostingPatchRequest,
    JobPostingResponseData,
    JobPostingApiResponse,
    JobPostingListApiResponse,
    JobPostingDeleteApiResponse,
)
from app.schemas.test_schemas import HelloResponse, SumResponse
from app.schemas.user_schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserPatchRequest,
    UserResponseData,
    UserApiResponse,
    UserListApiResponse,
    UserDeleteApiResponse,
)
from app.schemas.auth_schemas import (
    UserRegisterRequest,
    UserRegisterResponseData,
    UserRegisterApiResponse,
)

__all__ = [
    "AnnouncementCreateRequest",
    "AnnouncementUpdateRequest",
    "AnnouncementPatchRequest",
    "AnnouncementResponseData",
    "AnnouncementApiResponse",
    "AnnouncementListApiResponse",
    "AnnouncementDeleteApiResponse",
    "JobPostingCreateRequest",
    "JobPostingUpdateRequest",
    "JobPostingPatchRequest",
    "JobPostingResponseData",
    "JobPostingApiResponse",
    "JobPostingListApiResponse",
    "JobPostingDeleteApiResponse",
    "HelloResponse",
    "SumResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserPatchRequest",
    "UserResponseData",
    "UserApiResponse",
    "UserListApiResponse",
    "UserDeleteApiResponse",
    "UserRegisterRequest",
    "UserRegisterResponseData",
    "UserRegisterApiResponse",
]
