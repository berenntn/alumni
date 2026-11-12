# Database Design Document (DDD)

## Project
Alumni Management and Tracking System (İstanbul Üniversitesi Mezun Takip Sistemi)

## Database Infrastructure
- PostgreSQL 16 Alpine
- SQLAlchemy 2.0+ ORM
- Alembic Database Migrations

---

## Current Tables & Schemas

### 1. `users` Table
Relational table representing registered alumni users.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | Primary key, autoincrement | Unique user identifier |
| `name` | VARCHAR(255) | NOT NULL | Full name of the alumnus |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Unique email address |
| `department` | VARCHAR(255) | NOT NULL | Graduated department |
| `graduation_year` | INTEGER | NOT NULL | Year of graduation |
| `created_at` | TIMESTAMP | NOT NULL, default `utcnow` | Record creation timestamp |

### 2. `announcements` Table
University notices and alumni community announcements.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | Primary key, autoincrement, index | Unique announcement identifier |
| `title` | VARCHAR(255) | NOT NULL | Announcement title / subject |
| `content` | TEXT | NOT NULL | Body content |
| `created_by` | INTEGER | NULLABLE, FK `users.id` (ON DELETE SET NULL) | Author user ID |

### 3. `job_postings` Table
Employment and internship opportunities for alumni.

| Field | Type | Constraints & Validation | Description |
|---|---|---|---|
| `id` | INTEGER | Primary key, autoincrement | Unique job posting identifier |
| `title` | VARCHAR(255) | NOT NULL, Schema validation: Max 120 chars | Job title / position (Required) |
| `company_name` | VARCHAR(255) | NOT NULL, Schema validation: Min 1 char | Company / Organization name (Required) |
| `description` | TEXT | NULLABLE, default `""` in ORM | Role responsibilities (Optional) |
| `location` | VARCHAR(255) | NULLABLE | City / Location (Optional, accepts `city` alias) |
| `employment_type` | VARCHAR(50) | NULLABLE | Work arrangement (Optional: Full-time, Hybrid, etc.) |
| `created_at` | TIMESTAMP | NOT NULL, default `utcnow` | Posting timestamp |

### 4. `applications` Table
Job applications connecting alumni users to job postings.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | Primary key, autoincrement | Unique application identifier |
| `user_id` | INTEGER | NOT NULL, FK `users.id` | Alumnus applying for the role |
| `job_posting_id` | INTEGER | NOT NULL, FK `job_postings.id` | Target job posting |
| `status` | VARCHAR(20) | NOT NULL, default `'pending'` | Application state (`pending`, `accepted`, `rejected`) |
| `created_at` | TIMESTAMP | NOT NULL, default `utcnow` | Submission timestamp |

---

## Entity Relationships

```
┌───────────┐         1 : N          ┌─────────────────┐
│   users   ├───────────────────────►│  announcements  │
└─────┬─────┘                        └─────────────────┘
      │
      │ 1 : N
      ▼
┌──────────────┐      N : 1          ┌─────────────────┐
│ applications │◄────────────────────┤  job_postings   │
└──────────────┘                     └─────────────────┘
```

1. **User to Announcements (1:N):** One alumnus can publish multiple announcements. Foreign key `announcements.created_by -> users.id` with `ON DELETE SET NULL`.
2. **User to Applications (1:N):** One alumnus can apply for multiple jobs. Foreign key `applications.user_id -> users.id`.
3. **Job Posting to Applications (1:N):** One job posting can receive multiple alumni applications. Foreign key `applications.job_posting_id -> job_postings.id`.

---

## Job Application Functionality

The job application functionality is fully implemented and operational across both Web and REST API layers:

### 1. Web Interface Routes (`app/api/job_web_routes.py`)
- `GET /jobs`: Browse all available job postings.
- `GET /jobs/{job_id}/apply`: Interactive application form displaying job details.
- `POST /jobs/{job_id}/apply`: Submits application with applicant user ID; handles nonexistent user validation via PostgreSQL foreign key `IntegrityError` safely.
- `GET /applications`: Consolidated dashboard listing submitted applications with applicant and company details.

### 2. REST API Routes (`app/api/application_routes.py` & `app/api/application_nested_routes.py`)
- `GET /api/applications`: List all applications.
- `POST /api/applications`: Submit new application (`user_id`, `job_posting_id`).
- `GET /api/applications/{id}`: Retrieve application details.
- `PATCH /api/applications/{id}`: Update application status (`pending`, `accepted`, `rejected`).
- `DELETE /api/applications/{id}`: Delete an application.
- `GET /api/users/{user_id}/applications`: Nested route retrieving all applications by user.
- `GET /api/job-postings/{job_posting_id}/applications`: Nested route retrieving all applications for a job posting.

---

## Alembic Migration History

The schema evolution is tracked and managed via Alembic:

1. `6e2d08209d01`: `create_announcements_table` - Created `announcements` table.
2. `26154c96bb06`: `create_job_postings_table` - Created `job_postings` table.
3. `42053b92e130`: `create_users_table_and_announcement_` - Created `users` table and linked `announcements.created_by` foreign key.
4. `9aa14a4442a2`: `create_applications_table` - Created `applications` table with foreign keys to `users` and `job_postings`.
