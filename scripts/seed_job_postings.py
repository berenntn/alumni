"""Seed sample job postings without creating duplicates."""

from sqlalchemy import select

from app.core.database import get_db_session
from app.models.job_posting import JobPostingDB


SAMPLE_JOBS = [
    {
        "title": "Junior Python Developer",
        "company_name": "TechNova",
        "description": "Develop backend services using Python and FastAPI.",
        "location": "Istanbul",
        "employment_type": "Full-time",
    },
    {
        "title": "Frontend Developer",
        "company_name": "DigitalWorks",
        "description": "Build responsive web interfaces using React.",
        "location": "Remote",
        "employment_type": "Full-time",
    },
    {
        "title": "Data Analyst",
        "company_name": "DataBridge",
        "description": "Analyze datasets and prepare business reports.",
        "location": "Ankara",
        "employment_type": "Full-time",
    },
    {
        "title": "Software Engineering Intern",
        "company_name": "CloudBase",
        "description": "Support software development and testing activities.",
        "location": "Istanbul",
        "employment_type": "Internship",
    },
    {
        "title": "Backend Developer",
        "company_name": "CodeSphere",
        "description": "Design and maintain REST APIs and database integrations.",
        "location": "Izmir",
        "employment_type": "Hybrid",
    },
]


def seed_job_postings():
    added = 0

    with get_db_session() as session:
        for job in SAMPLE_JOBS:
            existing = session.scalar(
                select(JobPostingDB.id).where(
                    JobPostingDB.title == job["title"],
                    JobPostingDB.company_name == job["company_name"],
                )
            )

            if existing is None:
                session.add(JobPostingDB(**job))
                added += 1

    print(f"Eklenen iş ilanı: {added}")
    print(f"Atlanan mevcut ilan: {len(SAMPLE_JOBS) - added}")


if __name__ == "__main__":
    seed_job_postings()
