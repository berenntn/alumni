"""Web pages for job postings."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.job_posting import JobPostingDB

router = APIRouter(tags=["Job Pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/jobs")
def list_jobs_page(request: Request):
    """Display job postings from PostgreSQL."""
    with get_db_session() as session:
        jobs = session.scalars(
            select(JobPostingDB).order_by(JobPostingDB.id)
        ).all()

        job_data = [
            {
                "id": job.id,
                "title": job.title,
                "company_name": job.company_name,
                "description": job.description,
                "location": job.location,
                "employment_type": job.employment_type,
            }
            for job in jobs
        ]

    return templates.TemplateResponse(
        request=request,
        name="job_postings/list.html",
        context={
            "jobs": job_data,
            "app_name": "Alumni Tracking System",
            "app_title_tr": "Mezun Takip Sistemi",
        },
    )


from fastapi import HTTPException


@router.get("/jobs/{job_id}/apply")
def apply_job_page(request: Request, job_id: int):
    """Display the application form for a job posting."""
    with get_db_session() as session:
        job = session.get(JobPostingDB, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="İş ilanı bulunamadı.",
            )

        job_data = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
        }

    return templates.TemplateResponse(
        request=request,
        name="applications/apply.html",
        context={
            "job": job_data,
            "app_name": "Alumni Tracking System",
            "app_title_tr": "Mezun Takip Sistemi",
        },
    )


from fastapi import Form
from sqlalchemy.exc import IntegrityError

from app.models.application import ApplicationDB


@router.post("/jobs/{job_id}/apply")
def submit_job_application(
    request: Request,
    job_id: int,
    user_id: int = Form(..., ge=1),
):
    """Save a job application to PostgreSQL."""
    with get_db_session() as session:
        job = session.get(JobPostingDB, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="İş ilanı bulunamadı.",
            )

        job_data = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
        }

    try:
        with get_db_session() as session:
            application = ApplicationDB(
                user_id=user_id,
                job_posting_id=job_id,
                status="pending",
            )
            session.add(application)
            session.flush()

    except IntegrityError:
        return templates.TemplateResponse(
            request=request,
            name="applications/apply.html",
            context={
                "job": job_data,
                "app_name": "Alumni Tracking System",
                "app_title_tr": "Mezun Takip Sistemi",
                "error_message": (
                    "Kullanıcı numarası bulunamadı. "
                    "Lütfen kayıtlı bir kullanıcı numarası girin."
                ),
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="applications/apply.html",
        context={
            "job": job_data,
            "app_name": "Alumni Tracking System",
            "app_title_tr": "Mezun Takip Sistemi",
            "success_message": "Başvurunuz başarıyla kaydedildi!",
        },
    )


from app.models.user_db import UserDB


@router.get("/applications")
def list_applications_page(request: Request):
    """Display job applications with job and applicant details."""
    with get_db_session() as session:
        rows = session.execute(
            select(ApplicationDB, JobPostingDB, UserDB)
            .join(
                JobPostingDB,
                ApplicationDB.job_posting_id == JobPostingDB.id,
            )
            .join(
                UserDB,
                ApplicationDB.user_id == UserDB.id,
            )
            .order_by(ApplicationDB.id.desc())
        ).all()

        application_data = [
            {
                "id": application.id,
                "status": application.status,
                "job_title": job.title,
                "company_name": job.company_name,
                "user_name": user.name,
            }
            for application, job, user in rows
        ]

    return templates.TemplateResponse(
        request=request,
        name="applications/list.html",
        context={
            "applications": application_data,
            "app_name": "Alumni Tracking System",
            "app_title_tr": "Mezun Takip Sistemi",
        },
    )
