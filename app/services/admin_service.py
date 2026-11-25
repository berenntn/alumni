"""Admin service providing administrative operations, analytics, and safety guards.

Handles:
- System statistics aggregation from PostgreSQL.
- Initial admin account bootstrap and promotions.
- User management with search, filtering, and role changes.
- Safe deletion and demotion guards (Self-Deletion Protection, Last Admin Protection).
- Job postings, applications, and announcements administrative CRUD.
"""

from datetime import datetime
import logging
import math
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, or_, select

from app.core.database import get_db_session
from app.models.announcement import AnnouncementDB
from app.models.application import ApplicationDB
from app.models.job_posting import JobPostingDB
from app.models.user_db import UserDB
from app.services.announcement_service import AnnouncementService
from app.services.user_service import UserService

logger = logging.getLogger("app.services.admin")

ALLOWED_ROLES = {"admin", "academician", "alumnus", "student"}
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class AdminService:
    """Service coordinating administrative actions and role management."""

    # -------------------------------------------------------------------------
    # System Statistics
    # -------------------------------------------------------------------------
    @classmethod
    def get_system_stats(cls) -> Dict[str, int]:
        """Calculates real-time statistics aggregated directly from PostgreSQL."""
        with get_db_session() as db:
            total_users = db.scalar(select(func.count(UserDB.id))) or 0
            alumni_count = db.scalar(
                select(func.count(UserDB.id)).filter(UserDB.role == "alumnus")
            ) or 0
            students_count = db.scalar(
                select(func.count(UserDB.id)).filter(UserDB.role == "student")
            ) or 0
            academicians_count = db.scalar(
                select(func.count(UserDB.id)).filter(UserDB.role == "academician")
            ) or 0
            admins_count = db.scalar(
                select(func.count(UserDB.id)).filter(UserDB.role == "admin")
            ) or 0

            jobs_count = db.scalar(select(func.count(JobPostingDB.id))) or 0
            applications_count = db.scalar(select(func.count(ApplicationDB.id))) or 0
            announcements_count = db.scalar(select(func.count(AnnouncementDB.id))) or 0

        return {
            "total_users": total_users,
            "alumni_count": alumni_count,
            "students_count": students_count,
            "academicians_count": academicians_count,
            "admins_count": admins_count,
            "jobs_count": jobs_count,
            "applications_count": applications_count,
            "announcements_count": announcements_count,
        }

    # -------------------------------------------------------------------------
    # Initial Admin Bootstrap & Role Promotion
    # -------------------------------------------------------------------------
    @classmethod
    def promote_user_to_admin(cls, email: str) -> Dict[str, Any]:
        """Safely promotes an existing registered user to 'admin'.

        Idempotent and safe:
        - If user does not exist: reports clearly and DOES NOT create an account.
        - If user is already admin: reports safe status without modifying anything.
        - If user exists with another role: promotes to 'admin' without altering password.

        Args:
            email: Email address of user to promote.

        Returns:
            Dict containing status ('not_found', 'already_admin', 'promoted'), message, and user info.
        """
        normalized_email = (email or "").strip().lower()
        if not normalized_email:
            return {
                "status": "not_found",
                "message": "Geçerli bir e-posta adresi belirtilmedi.",
                "user": None,
            }

        with get_db_session() as db:
            user = db.query(UserDB).filter(func.lower(UserDB.email) == normalized_email).first()
            if not user:
                logger.warning(
                    f"Admin bootstrap: User with email '{normalized_email}' not found in database."
                )
                return {
                    "status": "not_found",
                    "message": f"User with email '{normalized_email}' not found in database. Please register at /register first.",
                    "user": None,
                }

            if user.role == "admin":
                logger.info(f"Admin bootstrap: User '{normalized_email}' is already an admin.")
                return {
                    "status": "already_admin",
                    "message": f"User '{normalized_email}' is already an admin.",
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "role": user.role,
                    },
                }

            # Promote existing user
            old_role = user.role
            user.role = "admin"
            db.flush()
            user_id = user.id
            user_name = user.name
            user_email = user.email

        # Mirror role in in-memory UserService
        try:
            mem_user = UserService.get_user(user_id)
            if mem_user:
                UserService.update_user(user_id, role="admin")
        except Exception as e:
            logger.debug(f"Note syncing role to UserService: {e}")

        logger.info(
            f"Admin bootstrap: User '{normalized_email}' (ID: {user_id}) promoted from '{old_role}' to 'admin'."
        )
        return {
            "status": "promoted",
            "message": f"User '{normalized_email}' successfully promoted to admin.",
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user_email,
                "role": "admin",
            },
        }

    # -------------------------------------------------------------------------
    # User Management (Listing, Search, Filter)
    # -------------------------------------------------------------------------
    @classmethod
    def list_users(
        cls,
        search: Optional[str] = None,
        role: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Queries users with optional search term, role filtering, and pagination.

        Guarantees:
        - Password hashes are strictly excluded from output.
        """
        page = max(1, page)
        per_page = max(1, min(100, per_page))

        with get_db_session() as db:
            query = db.query(UserDB)

            if search:
                pattern = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        UserDB.name.ilike(pattern),
                        UserDB.email.ilike(pattern),
                        UserDB.department.ilike(pattern),
                    )
                )

            if role and role.strip() and role.strip() != "all":
                query = query.filter(UserDB.role == role.strip())

            total = query.count()
            records = (
                query.order_by(UserDB.id.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            users = [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "department": u.department,
                    "graduation_year": u.graduation_year,
                    "role": u.role,
                    "created_at": u.created_at,
                }
                for u in records
            ]

        pages = max(1, math.ceil(total / per_page)) if total > 0 else 1
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    # -------------------------------------------------------------------------
    # Role Assignment & Safety Guards
    # -------------------------------------------------------------------------
    @classmethod
    def update_user_role(
        cls, target_user_id: int, new_role: str, current_admin_id: int
    ) -> Dict[str, Any]:
        """Updates user role with Last Admin Protection guard."""
        new_role = (new_role or "").strip().lower()
        if new_role not in ALLOWED_ROLES:
            raise ValueError(f"Geçersiz rol '{new_role}'. İzin verilen roller: {', '.join(sorted(ALLOWED_ROLES))}")

        with get_db_session() as db:
            target = db.get(UserDB, target_user_id)
            if not target:
                raise ValueError(f"ID {target_user_id} olan kullanıcı bulunamadı.")

            # Last Admin Demotion Guard
            if target.role == "admin" and new_role != "admin":
                admin_count = (
                    db.scalar(select(func.count(UserDB.id)).filter(UserDB.role == "admin")) or 0
                )
                if admin_count <= 1:
                    raise ValueError("Sistemdeki son yönetici hesabının rolü değiştirilemez.")

            old_role = target.role
            target.role = new_role
            db.flush()

            user_data = {
                "id": target.id,
                "name": target.name,
                "email": target.email,
                "department": target.department,
                "graduation_year": target.graduation_year,
                "role": target.role,
            }

        # Mirror role in in-memory UserService
        try:
            mem_user = UserService.get_user(target_user_id)
            if mem_user:
                UserService.update_user(target_user_id, role=new_role)
        except Exception:
            pass

        logger.info(
            f"Admin ID {current_admin_id} changed role of user ID {target_user_id} from '{old_role}' to '{new_role}'."
        )
        return user_data

    # -------------------------------------------------------------------------
    # User Details Update
    # -------------------------------------------------------------------------
    @classmethod
    def update_user_details(
        cls, target_user_id: int, data: Dict[str, Any], current_admin_id: int
    ) -> Dict[str, Any]:
        """Updates user details with validation and Last Admin Protection."""
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        department = (data.get("department") or "").strip()
        grad_year_raw = data.get("graduation_year")
        new_role = data.get("role")

        if not name or len(name) < 2:
            raise ValueError("Ad Soyad en az 2 karakter olmalıdır.")

        if not email or not EMAIL_REGEX.match(email):
            raise ValueError("Geçerli bir e-posta adresi giriniz.")

        if not department:
            raise ValueError("Bölüm bilgisi zorunludur.")

        try:
            graduation_year = int(grad_year_raw)
            if graduation_year < 1900 or graduation_year > 2100:
                raise ValueError()
        except Exception:
            raise ValueError("Mezuniyet yılı 1900 ile 2100 arasında geçerli bir yıl olmalıdır.")

        with get_db_session() as db:
            target = db.get(UserDB, target_user_id)
            if not target:
                raise ValueError(f"ID {target_user_id} olan kullanıcı bulunamadı.")

            # Check email uniqueness against other users
            existing_email = (
                db.query(UserDB)
                .filter(func.lower(UserDB.email) == email, UserDB.id != target_user_id)
                .first()
            )
            if existing_email:
                raise ValueError("Bu e-posta adresi başka bir kullanıcı tarafından kullanılmaktadır.")

            # If role is updated, enforce Last Admin Demotion guard
            if new_role and new_role.strip():
                resolved_role = new_role.strip().lower()
                if resolved_role not in ALLOWED_ROLES:
                    raise ValueError(f"Geçersiz rol '{resolved_role}'.")
                if target.role == "admin" and resolved_role != "admin":
                    admin_count = (
                        db.scalar(select(func.count(UserDB.id)).filter(UserDB.role == "admin")) or 0
                    )
                    if admin_count <= 1:
                        raise ValueError("Sistemdeki son yönetici hesabının rolü değiştirilemez.")
                target.role = resolved_role

            target.name = name
            target.email = email
            target.department = department
            target.graduation_year = graduation_year
            db.flush()

            updated_data = {
                "id": target.id,
                "name": target.name,
                "email": target.email,
                "department": target.department,
                "graduation_year": target.graduation_year,
                "role": target.role,
            }

        # Mirror in UserService
        try:
            UserService.update_user(
                target_user_id,
                name=updated_data["name"],
                email=updated_data["email"],
                department=updated_data["department"],
                graduation_year=updated_data["graduation_year"],
            )
        except Exception:
            pass

        return updated_data

    # -------------------------------------------------------------------------
    # User Deletion & Safety Guards
    # -------------------------------------------------------------------------
    @classmethod
    def delete_user(cls, target_user_id: int, current_admin_id: int) -> bool:
        """Deletes a user with Self-Deletion Protection and Last Admin Protection."""
        # 1. Self-Deletion Protection Guard
        if target_user_id == current_admin_id:
            raise ValueError("Kendi yönetici hesabınızı silemezsiniz.")

        with get_db_session() as db:
            target = db.get(UserDB, target_user_id)
            if not target:
                raise ValueError(f"ID {target_user_id} olan kullanıcı bulunamadı.")

            # 2. Last Admin Protection Guard
            if target.role == "admin":
                admin_count = (
                    db.scalar(select(func.count(UserDB.id)).filter(UserDB.role == "admin")) or 0
                )
                if admin_count <= 1:
                    raise ValueError("Sistemdeki son yönetici hesabı silinemez.")

            # Remove associated applications
            db.execute(delete(ApplicationDB).where(ApplicationDB.user_id == target_user_id))

            # Delete the user
            db.delete(target)
            db.flush()

        # Remove from in-memory UserService
        try:
            UserService.delete_user(target_user_id)
        except Exception:
            pass

        logger.info(
            f"Admin ID {current_admin_id} deleted user ID {target_user_id} from database."
        )
        return True

    # -------------------------------------------------------------------------
    # Job Postings Management
    # -------------------------------------------------------------------------
    @classmethod
    def list_jobs(cls) -> List[Dict[str, Any]]:
        """Returns all job postings ordered by ID descending with application counts."""
        with get_db_session() as db:
            jobs = db.scalars(select(JobPostingDB).order_by(JobPostingDB.id.desc())).all()
            result = []
            for j in jobs:
                app_count = (
                    db.scalar(
                        select(func.count(ApplicationDB.id)).filter(
                            ApplicationDB.job_posting_id == j.id
                        )
                    )
                    or 0
                )
                result.append(
                    {
                        "id": j.id,
                        "title": j.title,
                        "company_name": j.company_name,
                        "location": j.location,
                        "employment_type": j.employment_type,
                        "description": j.description,
                        "created_at": j.created_at,
                        "applications_count": app_count,
                    }
                )
        return result

    @classmethod
    def create_job(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new job posting from admin form."""
        title = (data.get("title") or "").strip()
        company_name = (data.get("company_name") or "").strip()
        location = (data.get("location") or "").strip() or None
        employment_type = (data.get("employment_type") or "").strip() or None
        description = (data.get("description") or "").strip()

        if not title:
            raise ValueError("İş ilanı başlığı zorunludur.")
        if len(title) > 120:
            raise ValueError("İş ilanı başlığı en fazla 120 karakter olabilir.")
        if not company_name:
            raise ValueError("Şirket adı zorunludur.")

        with get_db_session() as db:
            job = JobPostingDB(
                title=title,
                company_name=company_name,
                location=location,
                employment_type=employment_type,
                description=description,
                created_at=datetime.utcnow(),
            )
            db.add(job)
            db.flush()
            job_data = {
                "id": job.id,
                "title": job.title,
                "company_name": job.company_name,
                "location": job.location,
                "employment_type": job.employment_type,
                "description": job.description,
            }
        return job_data

    @classmethod
    def update_job(cls, job_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing job posting."""
        title = (data.get("title") or "").strip()
        company_name = (data.get("company_name") or "").strip()
        location = (data.get("location") or "").strip() or None
        employment_type = (data.get("employment_type") or "").strip() or None
        description = (data.get("description") or "").strip()

        if not title:
            raise ValueError("İş ilanı başlığı zorunludur.")
        if len(title) > 120:
            raise ValueError("İş ilanı başlığı en fazla 120 karakter olabilir.")
        if not company_name:
            raise ValueError("Şirket adı zorunludur.")

        with get_db_session() as db:
            job = db.get(JobPostingDB, job_id)
            if not job:
                raise ValueError(f"ID {job_id} olan iş ilanı bulunamadı.")

            job.title = title
            job.company_name = company_name
            job.location = location
            job.employment_type = employment_type
            job.description = description
            db.flush()
            job_data = {
                "id": job.id,
                "title": job.title,
                "company_name": job.company_name,
                "location": job.location,
                "employment_type": job.employment_type,
                "description": job.description,
            }
        return job_data

    @classmethod
    def delete_job(cls, job_id: int) -> bool:
        """Deletes a job posting and its associated applications."""
        with get_db_session() as db:
            job = db.get(JobPostingDB, job_id)
            if not job:
                raise ValueError(f"ID {job_id} olan iş ilanı bulunamadı.")

            db.execute(
                delete(ApplicationDB).where(ApplicationDB.job_posting_id == job_id)
            )
            db.delete(job)
            db.flush()
        return True

    # -------------------------------------------------------------------------
    # Applications Review & Management
    # -------------------------------------------------------------------------
    @classmethod
    def list_applications(cls) -> List[Dict[str, Any]]:
        """Returns all job applications with applicant and job posting information."""
        with get_db_session() as db:
            rows = (
                db.execute(
                    select(ApplicationDB, JobPostingDB, UserDB)
                    .join(JobPostingDB, ApplicationDB.job_posting_id == JobPostingDB.id)
                    .join(UserDB, ApplicationDB.user_id == UserDB.id)
                    .order_by(ApplicationDB.id.desc())
                )
                .all()
            )

            applications = [
                {
                    "id": app.id,
                    "status": app.status,
                    "created_at": app.created_at,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "user_department": user.department,
                    "job_id": job.id,
                    "job_title": job.title,
                    "job_company": job.company_name,
                }
                for app, job, user in rows
            ]
        return applications

    @classmethod
    def update_application_status(cls, application_id: int, new_status: str) -> Dict[str, Any]:
        """Updates the status of an application (e.g. pending, accepted, rejected)."""
        valid_statuses = {"pending", "accepted", "rejected", "applied"}
        new_status = (new_status or "").strip().lower()
        if new_status not in valid_statuses:
            raise ValueError(f"Geçersiz başvuru durumu '{new_status}'.")

        with get_db_session() as db:
            app = db.get(ApplicationDB, application_id)
            if not app:
                raise ValueError(f"ID {application_id} olan başvuru bulunamadı.")

            app.status = new_status
            db.flush()
            result = {"id": app.id, "status": app.status}
        return result

    @classmethod
    def delete_application(cls, application_id: int) -> bool:
        """Deletes an application."""
        with get_db_session() as db:
            app = db.get(ApplicationDB, application_id)
            if not app:
                raise ValueError(f"ID {application_id} olan başvuru bulunamadı.")

            db.delete(app)
            db.flush()
        return True

    # -------------------------------------------------------------------------
    # Announcements Management
    # -------------------------------------------------------------------------
    @classmethod
    def list_announcements(cls) -> List[Dict[str, Any]]:
        """Returns all announcements with author details."""
        announcements = AnnouncementService.get_announcements()
        with get_db_session() as db:
            users_map = {
                u.id: u.name for u in db.query(UserDB.id, UserDB.name).all()
            }

        result = []
        for a in announcements:
            result.append(
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "created_by": a.created_by,
                    "author_name": users_map.get(a.created_by, "Sistem") if a.created_by else "Sistem",
                }
            )
        return result

    @classmethod
    def create_announcement(cls, data: Dict[str, Any], admin_user_id: int) -> Dict[str, Any]:
        """Creates a new announcement as admin."""
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        if not title:
            raise ValueError("Duyuru başlığı zorunludur.")
        if not content:
            raise ValueError("Duyuru içeriği zorunludur.")

        created = AnnouncementService.create_announcement(
            title=title, content=content, created_by=admin_user_id
        )
        return {"id": created.id, "title": created.title, "content": created.content}

    @classmethod
    def update_announcement(cls, announcement_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing announcement."""
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        if not title:
            raise ValueError("Duyuru başlığı zorunludur.")
        if not content:
            raise ValueError("Duyuru içeriği zorunludur.")

        updated = AnnouncementService.update_announcement(
            announcement_id=announcement_id, title=title, content=content
        )
        if not updated:
            raise ValueError(f"ID {announcement_id} olan duyuru bulunamadı.")
        return {"id": updated.id, "title": updated.title, "content": updated.content}

    @classmethod
    def delete_announcement(cls, announcement_id: int) -> bool:
        """Deletes an announcement."""
        deleted = AnnouncementService.delete_announcement(announcement_id)
        if not deleted:
            raise ValueError(f"ID {announcement_id} olan duyuru bulunamadı.")
        return True
