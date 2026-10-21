"""Tests for the job posting seed script."""

import unittest
from unittest.mock import MagicMock, patch

from scripts.seed_job_postings import SAMPLE_JOBS, seed_job_postings


class TestSeedJobPostings(unittest.TestCase):

    def test_five_sample_jobs_defined(self):
        self.assertEqual(len(SAMPLE_JOBS), 5)

    def test_sample_jobs_have_required_fields(self):
        for job in SAMPLE_JOBS:
            self.assertTrue(job["title"])
            self.assertTrue(job["company_name"])
            self.assertTrue(job["description"])

    @patch("scripts.seed_job_postings.get_db_session")
    def test_existing_jobs_are_not_duplicated(self, mock_db):
        session = MagicMock()
        mock_db.return_value.__enter__.return_value = session
        session.scalar.return_value = 1

        seed_job_postings()

        self.assertEqual(session.add.call_count, 0)

    @patch("scripts.seed_job_postings.get_db_session")
    def test_missing_jobs_are_added(self, mock_db):
        session = MagicMock()
        mock_db.return_value.__enter__.return_value = session
        session.scalar.return_value = None

        seed_job_postings()

        self.assertEqual(session.add.call_count, 5)


if __name__ == "__main__":
    unittest.main()
