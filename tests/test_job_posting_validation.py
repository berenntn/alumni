"""Unit and integration tests for Job Posting validation, schemas, and REST API routes."""

import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.database import Base, get_db_session, get_engine
from app.main import app
from app.models.job_posting import JobPosting, JobPostingDB
from app.models.user_db import UserDB
from app.services.session_service import SessionService, clear_sessions
from app.schemas.job_posting_schemas import (
    JobPostingCreateRequest,
    JobPostingPatchRequest,
    JobPostingUpdateRequest,
)


class TestJobPostingValidation(unittest.TestCase):
    """Test suite verifying Job Posting validation rules and compatibility."""

    @classmethod
    def setUpClass(cls):
        """Ensure test database tables are created."""
        engine = get_engine()
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        with get_db_session() as db:
            db.query(UserDB).filter(UserDB.email == "admin@alumni.test").delete()
            admin = UserDB(
                id=1,
                name="Admin Test",
                email="admin@alumni.test",
                department="Bilgisayar",
                graduation_year=2020,
                role="admin",
            )
            db.merge(admin)
            db.flush()
        token = SessionService.create_session(admin)
        self.client = TestClient(app)
        self.client.headers["Authorization"] = f"Bearer {token}"

    def tearDown(self):
        clear_sessions()
        with get_db_session() as db:
            db.query(UserDB).filter(UserDB.email == "admin@alumni.test").delete()

    # -------------------------------------------------------------------------
    # Pydantic Schema Validation Tests
    # -------------------------------------------------------------------------

    def test_valid_job_posting_all_fields(self):
        """Verify successful schema creation when all fields are provided."""
        payload = {
            "title": "Senior Python Engineer",
            "company_name": "Tech Corp",
            "location": "Istanbul",
            "description": "Building scalable microservices.",
            "employment_type": "Full-time",
        }
        model = JobPostingCreateRequest(**payload)
        self.assertEqual(model.title, "Senior Python Engineer")
        self.assertEqual(model.company_name, "Tech Corp")
        self.assertEqual(model.location, "Istanbul")
        self.assertEqual(model.description, "Building scalable microservices.")
        self.assertEqual(model.employment_type, "Full-time")

    def test_title_max_120_characters_boundary(self):
        """Title with exactly 120 characters should be valid."""
        exact_120 = "A" * 120
        model = JobPostingCreateRequest(
            title=exact_120,
            company_name="Valid Corp",
        )
        self.assertEqual(len(model.title), 120)

    def test_title_exceeding_120_characters_fails(self):
        """Title with 121 characters must raise a ValidationError."""
        too_long = "A" * 121
        with self.assertRaises(ValidationError) as ctx:
            JobPostingCreateRequest(
                title=too_long,
                company_name="Valid Corp",
            )
        self.assertIn("title", str(ctx.exception))

    def test_title_missing_or_empty_fails(self):
        """Missing or empty title must fail validation."""
        with self.assertRaises(ValidationError):
            JobPostingCreateRequest(
                title="",
                company_name="Valid Corp",
            )

        with self.assertRaises(ValidationError):
            JobPostingCreateRequest(
                company_name="Valid Corp",
            )

    def test_company_name_required(self):
        """Missing or empty company_name must fail validation."""
        with self.assertRaises(ValidationError):
            JobPostingCreateRequest(
                title="Backend Developer",
                company_name="",
            )

        with self.assertRaises(ValidationError):
            JobPostingCreateRequest(
                title="Backend Developer",
            )

    def test_location_and_city_optional_fallback(self):
        """City alias should automatically populate location if location is omitted."""
        # Neither location nor city
        m1 = JobPostingCreateRequest(
            title="DevOps Engineer",
            company_name="CloudNet",
        )
        self.assertIsNone(m1.location)

        # Using city
        m2 = JobPostingCreateRequest(
            title="DevOps Engineer",
            company_name="CloudNet",
            city="Izmir",
        )
        self.assertEqual(m2.location, "Izmir")

        # Explicit location takes precedence
        m3 = JobPostingCreateRequest(
            title="DevOps Engineer",
            company_name="CloudNet",
            location="Ankara",
            city="Izmir",
        )
        self.assertEqual(m3.location, "Ankara")

    def test_description_optional(self):
        """Description should be optional and default to empty string."""
        model = JobPostingCreateRequest(
            title="Frontend Developer",
            company_name="WebWorks",
        )
        self.assertEqual(model.description, "")

    def test_domain_job_posting_model_validation(self):
        """Domain JobPosting model should enforce max 120 chars and required company."""
        domain_job = JobPosting(
            title="QA Automation Lead",
            company_name="QualityFirst",
        )
        self.assertEqual(domain_job.title, "QA Automation Lead")
        self.assertEqual(domain_job.company_name, "QualityFirst")
        self.assertEqual(domain_job.description, "")

        with self.assertRaises(ValidationError):
            JobPosting(
                title="B" * 121,
                company_name="QualityFirst",
            )

    # -------------------------------------------------------------------------
    # API Integration Tests (/api/job-postings)
    # -------------------------------------------------------------------------

    def test_api_create_job_posting_success(self):
        """POST /api/job-postings should create job and return 201 Created."""
        payload = {
            "title": "Machine Learning Engineer",
            "company_name": "DataWorks AI",
            "location": "Remote",
            "description": "Training transformer models.",
            "employment_type": "Full-time",
        }
        res = self.client.post("/api/job-postings", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["title"], "Machine Learning Engineer")
        self.assertEqual(data["data"]["company_name"], "DataWorks AI")
        self.assertIsNotNone(data["data"]["id"])

    def test_api_create_job_posting_with_optional_fields_omitted(self):
        """POST /api/job-postings should succeed when location and description are omitted."""
        payload = {
            "title": "Junior Python Developer",
            "company_name": "StartUp Hub",
        }
        res = self.client.post("/api/job-postings", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["title"], "Junior Python Developer")
        self.assertEqual(data["data"]["company_name"], "StartUp Hub")
        self.assertEqual(data["data"]["description"], "")
        self.assertIsNone(data["data"]["location"])

    def test_api_create_job_posting_title_too_long_returns_422(self):
        """POST /api/job-postings with title > 120 chars should return 422."""
        payload = {
            "title": "T" * 121,
            "company_name": "Tech Corp",
        }
        res = self.client.post("/api/job-postings", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_api_create_job_posting_missing_title_returns_422(self):
        """POST /api/job-postings without title should return 422."""
        payload = {
            "company_name": "Tech Corp",
        }
        res = self.client.post("/api/job-postings", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_api_create_job_posting_missing_company_name_returns_422(self):
        """POST /api/job-postings without company_name should return 422."""
        payload = {
            "title": "Backend Developer",
        }
        res = self.client.post("/api/job-postings", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_api_get_job_postings_list(self):
        """GET /api/job-postings should return list of job postings."""
        res = self.client.get("/api/job-postings")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)
        self.assertGreaterEqual(data["count"], 0)

    def test_api_get_single_job_posting(self):
        """GET /api/job-postings/{id} should return 200 for existing and 404 for missing."""
        # Create one first
        create_res = self.client.post(
            "/api/job-postings",
            json={"title": "Cloud Architect", "company_name": "SkyNet"},
        )
        job_id = create_res.json()["data"]["id"]

        # Fetch existing
        get_res = self.client.get(f"/api/job-postings/{job_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["data"]["title"], "Cloud Architect")

        # Fetch missing
        missing_res = self.client.get("/api/job-postings/999999")
        self.assertEqual(missing_res.status_code, 404)
        self.assertEqual(missing_res.json()["status"], "error")

    def test_api_update_job_posting_put(self):
        """PUT /api/job-postings/{id} should fully update job posting."""
        create_res = self.client.post(
            "/api/job-postings",
            json={"title": "Intern", "company_name": "BaseCo"},
        )
        job_id = create_res.json()["data"]["id"]

        # Full update
        update_payload = {
            "title": "Full-Time Engineer",
            "company_name": "BaseCo Advanced",
            "location": "Bursa",
            "description": "Full responsibilities.",
            "employment_type": "Full-time",
        }
        update_res = self.client.put(f"/api/job-postings/{job_id}", json=update_payload)
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["data"]["title"], "Full-Time Engineer")
        self.assertEqual(update_res.json()["data"]["company_name"], "BaseCo Advanced")

        # Update with title > 120 chars fails
        bad_res = self.client.put(
            f"/api/job-postings/{job_id}",
            json={"title": "X" * 121, "company_name": "BaseCo"},
        )
        self.assertEqual(bad_res.status_code, 422)

    def test_api_patch_job_posting(self):
        """PATCH /api/job-postings/{id} should partially update job posting."""
        create_res = self.client.post(
            "/api/job-postings",
            json={"title": "Data Scientist", "company_name": "Analytics Co"},
        )
        job_id = create_res.json()["data"]["id"]

        patch_res = self.client.patch(
            f"/api/job-postings/{job_id}",
            json={"location": "Eskisehir"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["data"]["title"], "Data Scientist")
        self.assertEqual(patch_res.json()["data"]["location"], "Eskisehir")

    def test_api_delete_job_posting(self):
        """DELETE /api/job-postings/{id} should delete job posting."""
        create_res = self.client.post(
            "/api/job-postings",
            json={"title": "Temporary Role", "company_name": "TempCorp"},
        )
        job_id = create_res.json()["data"]["id"]

        del_res = self.client.delete(f"/api/job-postings/{job_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()["status"], "success")

        # Verify subsequent GET returns 404
        get_res = self.client.get(f"/api/job-postings/{job_id}")
        self.assertEqual(get_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
