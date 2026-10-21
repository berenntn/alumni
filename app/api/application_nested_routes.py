"""Nested routes for job applications."""

from fastapi import APIRouter, Path
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.application import ApplicationDB


router = APIRouter(tags=["Application Nested Routes"])


def serialize_application(item):
    return {
        "id": item.id,
        "user_id": item.user_id,
        "job_posting_id": item.job_posting_id,
        "status": item.status,
        "created_at": item.created_at,
    }


@router.get("/api/users/{user_id}/applications")
def get_user_applications(user_id: int = Path(..., ge=1)):
    """List applications submitted by a user."""
    with get_db_session() as session:
        applications = session.execute(
            select(ApplicationDB)
            .where(ApplicationDB.user_id == user_id)
            .order_by(ApplicationDB.id)
        ).scalars().all()

        return [serialize_application(item) for item in applications]


@router.get("/api/job-postings/{job_posting_id}/applications")
def get_job_posting_applications(
    job_posting_id: int = Path(..., ge=1),
):
    """List applications for a job posting."""
    with get_db_session() as session:
        applications = session.execute(
            select(ApplicationDB)
            .where(ApplicationDB.job_posting_id == job_posting_id)
            .order_by(ApplicationDB.id)
        ).scalars().all()

        return [serialize_application(item) for item in applications]
