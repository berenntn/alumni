# Database Design Document (DDD)

## Project
Alumni Management and Tracking System

## Database
- PostgreSQL 16
- SQLAlchemy ORM
- Alembic migrations

## Current Tables

### 1. announcements
Existing table for university announcements.

Fields:
- id: INTEGER, primary key
- title: VARCHAR(255), required
- content: TEXT, required
- created_by: INTEGER, optional

### 2. job_postings
New table for job opportunities shared with alumni.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key, auto-increment |
| title | VARCHAR(255) | NOT NULL |
| company_name | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| location | VARCHAR(255) | NULL allowed |
| employment_type | VARCHAR(50) | NULL allowed |
| created_at | TIMESTAMP | NOT NULL, default current time |

## Relationships

The `job_postings` table is initially independent.

The User model currently uses in-memory storage, so no
foreign key to a users table is defined yet.

## Migration Strategy

- Create the SQLAlchemy JobPostingDB model.
- Generate an Alembic migration for job_postings.
- Apply the migration using `alembic upgrade head`.
- Preserve existing announcements and their data.

## Future Improvements

- Associate job postings with registered alumni.
- Add job application functionality.
- Add filtering by company, location, and employment type.
