"""REST API routes for job applications."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db_session
from app.models.application import ApplicationDB


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"],
)


class ApplicationCreateRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    job_posting_id: int = Field(..., ge=1)


@router.get("")
def list_applications():
    """List all job applications."""
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
def create_application(payload: ApplicationCreateRequest):
    """Create a job application."""
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
def get_application(application_id: int):
    """Get an application by ID."""
    with get_db_session() as session:
        application = session.get(ApplicationDB, application_id)

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        return {
            "id": application.id,
            "user_id": application.user_id,
            "job_posting_id": application.job_posting_id,
            "status": application.status,
            "created_at": application.created_at,
        }


@router.patch("/{application_id}")
def update_application(
    application_id: int,
    payload: ApplicationUpdateRequest,
):
    """Update an application's status."""
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
def delete_application(application_id: int):
    """Delete an application."""
    with get_db_session() as session:
        application = session.get(ApplicationDB, application_id)

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        session.delete(application)

        return {"message": "Application deleted successfully."}
