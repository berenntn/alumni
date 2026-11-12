"""REST API routes for Job Postings management."""

from fastapi import APIRouter, HTTPException, Path as PathParam, status
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.job_posting import JobPostingDB
from app.schemas.job_posting_schemas import (
    JobPostingCreateRequest,
    JobPostingUpdateRequest,
    JobPostingPatchRequest,
    JobPostingResponseData,
    JobPostingApiResponse,
    JobPostingListApiResponse,
    JobPostingDeleteApiResponse,
)

router = APIRouter(
    prefix="/api/job-postings",
    tags=["Job Postings"],
)


def _serialize_job(job: JobPostingDB) -> JobPostingResponseData:
    """Helper to convert a JobPostingDB model to JobPostingResponseData."""
    return JobPostingResponseData(
        id=job.id,
        title=job.title,
        company_name=job.company_name,
        location=job.location,
        description=job.description or "",
        employment_type=job.employment_type,
        created_at=job.created_at,
    )


@router.get(
    "",
    response_model=JobPostingListApiResponse,
    summary="List All Job Postings",
    description="Retrieves a list of all job postings stored in PostgreSQL.",
)
@router.get(
    "/",
    response_model=JobPostingListApiResponse,
    include_in_schema=False,
)
def list_job_postings():
    """Retrieve all job postings."""
    with get_db_session() as session:
        jobs = session.scalars(
            select(JobPostingDB).order_by(JobPostingDB.id)
        ).all()

        items = [_serialize_job(job) for job in jobs]

        return JobPostingListApiResponse(
            status="success",
            message=f"Retrieved {len(items)} job postings",
            data=items,
            count=len(items),
        )


@router.post(
    "",
    response_model=JobPostingApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Posting",
    description="Creates a new job posting with validation (title max 120 chars, company required).",
)
@router.post(
    "/",
    response_model=JobPostingApiResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_job_posting(payload: JobPostingCreateRequest):
    """Create a new job posting in PostgreSQL."""
    location_val = payload.location or payload.city or None
    description_val = payload.description or ""

    with get_db_session() as session:
        job = JobPostingDB(
            title=payload.title,
            company_name=payload.company_name,
            location=location_val,
            description=description_val,
            employment_type=payload.employment_type,
        )
        session.add(job)
        session.flush()

        data = _serialize_job(job)

        return JobPostingApiResponse(
            status="success",
            message="Job posting created successfully",
            data=data,
        )


@router.get(
    "/{id}",
    response_model=JobPostingApiResponse,
    summary="Get Job Posting by ID",
    description="Retrieves a specific job posting by unique ID.",
)
def get_job_posting(
    id: int = PathParam(..., description="Unique integer ID of the job posting", examples=[1]),
):
    """Retrieve a single job posting by ID."""
    with get_db_session() as session:
        job = session.get(JobPostingDB, id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found.",
            )

        return JobPostingApiResponse(
            status="success",
            message="Job posting retrieved successfully",
            data=_serialize_job(job),
        )


@router.put(
    "/{id}",
    response_model=JobPostingApiResponse,
    summary="Full Update Job Posting",
    description="Fully updates an existing job posting.",
)
def update_job_posting(
    payload: JobPostingUpdateRequest,
    id: int = PathParam(..., description="Unique integer ID of the job posting", examples=[1]),
):
    """Fully update a job posting."""
    location_val = payload.location or payload.city or None
    description_val = payload.description or ""

    with get_db_session() as session:
        job = session.get(JobPostingDB, id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found.",
            )

        job.title = payload.title
        job.company_name = payload.company_name
        job.location = location_val
        job.description = description_val
        job.employment_type = payload.employment_type

        session.flush()

        return JobPostingApiResponse(
            status="success",
            message="Job posting updated successfully",
            data=_serialize_job(job),
        )


@router.patch(
    "/{id}",
    response_model=JobPostingApiResponse,
    summary="Partial Update Job Posting",
    description="Partially updates specified fields of an existing job posting.",
)
def patch_job_posting(
    payload: JobPostingPatchRequest,
    id: int = PathParam(..., description="Unique integer ID of the job posting", examples=[1]),
):
    """Partially update a job posting."""
    with get_db_session() as session:
        job = session.get(JobPostingDB, id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found.",
            )

        update_dict = payload.model_dump(exclude_unset=True)

        if "city" in update_dict and "location" not in update_dict:
            update_dict["location"] = update_dict.pop("city")
        elif "city" in update_dict:
            update_dict.pop("city")

        for key, val in update_dict.items():
            setattr(job, key, val)

        session.flush()

        return JobPostingApiResponse(
            status="success",
            message="Job posting updated successfully",
            data=_serialize_job(job),
        )


@router.delete(
    "/{id}",
    response_model=JobPostingDeleteApiResponse,
    summary="Delete Job Posting",
    description="Deletes a job posting from PostgreSQL.",
)
def delete_job_posting(
    id: int = PathParam(..., description="Unique integer ID of the job posting", examples=[1]),
):
    """Delete a job posting."""
    with get_db_session() as session:
        job = session.get(JobPostingDB, id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found.",
            )

        session.delete(job)

        return JobPostingDeleteApiResponse(
            status="success",
            message="Job posting deleted successfully",
        )
