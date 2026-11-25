"""REST API routes for job applications."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, require_role
from app.models.application import ApplicationDB


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"],
)


class ApplicationCreateRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    job_posting_id: int = Field(..., ge=1)


@router.get("", dependencies=[Depends(require_role("admin"))])
def list_applications():
    """List all job applications (Admin only)."""
    with get_db_session() as session:
        applications = session.execute(
            select(ApplicationDB).order_by(ApplicationDB.id)
        ).scalars().all()

        return [
            {
                "id": item.id,
                "user_id": item.user_id,
                "job_posting_id": item.job_posting_id,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in applications
        ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a job application (Applicant self or Admin)."""
    if current_user.get("role") != "admin" and payload.user_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yalnızca kendi adınıza başvuru yapabilirsiniz.",
        )

    try:
        with get_db_session() as session:
            application = ApplicationDB(
                user_id=payload.user_id,
                job_posting_id=payload.job_posting_id,
                status="pending",
            )

            session.add(application)
            session.flush()

            return {
                "id": application.id,
                "user_id": application.user_id,
                "job_posting_id": application.job_posting_id,
                "status": application.status,
            }
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="User or job posting does not exist.",
        )


class ApplicationUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(pending|accepted|rejected)$",
    )


@router.get("/{application_id}")
def get_application(
    application_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get an application by ID (Applicant owner or Admin)."""
    with get_db_session() as session:
        application = session.get(ApplicationDB, application_id)

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        if application.user_id != current_user.get("user_id") and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu başvuruyu görüntüleme yetkiniz bulunmamaktadır.",
            )

        return {
            "id": application.id,
            "user_id": application.user_id,
            "job_posting_id": application.job_posting_id,
            "status": application.status,
            "created_at": application.created_at,
        }


@router.patch("/{application_id}", dependencies=[Depends(require_role("admin"))])
def update_application(
    application_id: int,
    payload: ApplicationUpdateRequest,
):
    """Update an application's status (Admin only)."""
    with get_db_session() as session:
        application = session.get(ApplicationDB, application_id)

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        application.status = payload.status
        session.flush()

        return {
            "id": application.id,
            "status": application.status,
        }


@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete an application (Applicant owner or Admin)."""
    with get_db_session() as session:
        application = session.get(ApplicationDB, application_id)

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        if application.user_id != current_user.get("user_id") and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu başvuruyu silme yetkiniz bulunmamaktadır.",
            )

        session.delete(application)

        return {"message": "Application deleted successfully."}
