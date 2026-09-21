from html import escape
from services.webhook_service import WebhookService
import logging
import os

from extensions import db, cache
from models.job import JobApplication, ApplicationStatus
from models.user import User

from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)

from services.email_service import send_email
def sanitize_notes(notes):
    if notes is None:
        return None
    return escape(str(notes))


# =========================
# Logger Setup
# =========================
logger = logging.getLogger(__name__)


class ApplicationService:
    # =========================
    # Create Application
    # =========================
    @staticmethod
    def create_application(data, user_id):


        logger.info(
            "Creating application for company: %s",
            data.get("company")
        )

        existing_application = JobApplication.query.filter_by(
            company=data["company"],
            role=data["role"],
            user_id=user_id
        ).first()

        if existing_application:

            logger.warning(
                "Duplicate application attempt: %s - %s",
                data["company"],
                data["role"]
            )

            raise DuplicateApplication(
                "This job application already exists."
            )

        new_application = JobApplication(
            company=data["company"],
            role=data["role"],
            status=data.get(
                "status",
                ApplicationStatus.APPLIED
            ),
            interview_at=data.get("interview_at"),
            notes=sanitize_notes(data.get("notes")),
            user_id=user_id
        )

        db.session.add(new_application)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        logger.info(
            "Application created successfully with ID: %s",
            new_application.id
        )

        cache.delete(f"analytics:user:{user_id}")

        return new_application


    # =========================
    # Get All Applications
    # =========================
    @staticmethod
    def get_all_applications(
        user_id,
        search=None,
        status=None,
        sort="newest",
        page=1,
        per_page=5
    ):

        logger.info(
            "Fetching applications for user ID: %s",
            user_id
        )

        query = JobApplication.query.filter_by(
            user_id=user_id
        )

        # Search
        if search:

            search_term = f"%{search}%"

            query = query.filter(
                db.or_(
                    JobApplication.company.ilike(search_term),
                    JobApplication.role.ilike(search_term)
                )
            )

        # Filter by status
        if status:

            query = query.filter(
                JobApplication.status == status
            )

        # Sorting
        if sort == "oldest":

            query = query.order_by(
                JobApplication.applied_date.asc()
            )

        elif sort == "company":

            query = query.order_by(
                JobApplication.company.asc()
            )

        else:

            query = query.order_by(
                JobApplication.applied_date.desc()
            )

        # Pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return pagination


    # =========================
    # Get Application By ID
    # =========================
    @staticmethod
    def get_application_by_id(application_id, user_id):

        application = JobApplication.query.filter_by(
            id=application_id,
            user_id=user_id
        ).first()

        if not application:

            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        return application

    @staticmethod
    def get_application_by_resume_filename(filename, user_id):
        """Find a user-owned application by its stored resume filename."""
        application = JobApplication.query.filter_by(user_id=user_id).filter(
            JobApplication.resume_path.like(f"%{filename}")
        ).first()
        if not application:
            raise ApplicationNotFound("Resume file not found.")
        return application

    @staticmethod
    def set_resume_path(application_id, user_id, resume_path):
        """Persist a resume path through the service layer."""
        application = ApplicationService.get_application_by_id(application_id, user_id)
        previous_path = application.resume_path
        application.resume_path = resume_path
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return previous_path


    # =========================
    # Update Application
    # =========================
    @staticmethod
    def update_application(application_id, data, user_id):

        application = JobApplication.query.filter_by(
            id=application_id,
            user_id=user_id
        ).first()

        if not application:

            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        # =========================
        # Save Old Status
        # =========================
        old_status = application.status

        # =========================
        # Update Fields
        # =========================
        application.company = data.get(
            "company",
            application.company
        )

        application.role = data.get(
            "role",
            application.role
        )

        application.status = data.get(
            "status",
            application.status
        )

        if "interview_at" in data:

           application.interview_at = data["interview_at"]
           application.interview_reminder_sent_at = None

        application.notes = sanitize_notes(
           data.get("notes", application.notes)
        )

        if "applied_date" in data:

            application.applied_date = data["applied_date"]

        # =========================
        # Save Changes
        # =========================
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # =========================
        # Send Email When Status Changes
        # =========================
        if old_status != application.status:
            if application.status == ApplicationStatus.OFFER:
                WebhookService.send_slack_offer_notification(application)

            user = db.session.get(User, user_id)

            if user and user.email:

                send_email(
                    subject="Job Application Status Updated",
                    recipients=[user.email],
                    body=(
                        f"Hello {user.name},\n\n"
                        f"Your job application status has been updated.\n\n"
                        f"Company: {application.company}\n"
                        f"Role: {application.role}\n"
                        f"Previous Status: {old_status.value}\n"
                        f"New Status: {application.status.value}\n\n"
                        f"Job Application Tracker"
                    )
                )

            # Send Webhook When Status Changes
            WebhookService.send_status_change(
                application=application,
                old_status=old_status,
                new_status=application.status
            )

        logger.info(
            "Application updated successfully: %s",
            application_id
        )

        cache.delete(f"analytics:user:{user_id}")

        return application

     

   
    # =========================
    # Bulk Status Update
    # =========================
    @staticmethod
    def bulk_update_status(application_ids, status, user_id):

        applications = JobApplication.query.filter(
            JobApplication.id.in_(application_ids),
            JobApplication.user_id == user_id
        ).all()

        applications_by_id = {
            application.id: application
            for application in applications
        }

        updated_ids = []
        failed = []

        for application_id in application_ids:
            application = applications_by_id.get(application_id)

            if not application:
                failed.append({
                    "id": application_id,
                    "error": (
                        f"Application with ID {application_id} "
                        "not found for current user"
                    )
                })
                continue

            application.status = status
            updated_ids.append(application_id)

        try:
            db.session.commit()
            cache.delete(f"analytics:user:{user_id}")
        except Exception:
            db.session.rollback()
            raise

        return {
            "updated": len(updated_ids),
            "updated_ids": updated_ids,
            "failed": len(failed),
            "errors": failed
        }


    # =========================
    # Delete Application
    # Delete Resume File
    # =========================
    @staticmethod
    def delete_application(application_id, user_id):

        logger.info(
            "Deleting application ID: %s",
            application_id
        )

        application = JobApplication.query.filter_by(
            id=application_id,
            user_id=user_id
        ).first()

        if not application:

            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        # =========================
        # Delete Resume File
        # =========================
        if application.resume_path:

            if os.path.exists(
                application.resume_path
            ):

                os.remove(
                    application.resume_path
                )

                logger.info(
                    "Resume file deleted: %s",
                    application.resume_path
                )

            else:

                logger.warning(
                    "Resume file not found: %s",
                    application.resume_path
                )

        # =========================
        # Delete Application
        # =========================
        db.session.delete(application)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        logger.info(
            "Application and resume deleted successfully: %s",
            application_id
        )

        cache.delete(f"analytics:user:{user_id}")

        return True


    # =========================
    # Dashboard Statistics
    # =========================
    @staticmethod
    def get_dashboard_statistics(user_id):

        applications = JobApplication.query.filter_by(
            user_id=user_id
        ).all()

        total_applications = len(applications)

        applied = sum(
            1
            for application in applications
            if application.status == ApplicationStatus.APPLIED
        )

        phone_screen = sum(
            1
            for application in applications
            if application.status == ApplicationStatus.PHONE_SCREEN
        )

        interview = sum(
            1
            for application in applications
            if application.status == ApplicationStatus.INTERVIEW
        )

        rejected = sum(
            1
            for application in applications
            if application.status == ApplicationStatus.REJECTED
        )

        offered = sum(
            1
            for application in applications
            if application.status == ApplicationStatus.OFFER
        )

        return {
            "total_applications": total_applications,
            "applied": applied,
            "phone_screen": phone_screen,
            "interview": interview,
            "rejected": rejected,
            "offered": offered,
            "by_status": {
                "APPLIED": applied,
                "PHONE_SCREEN": phone_screen,
                "INTERVIEW": interview,
                "OFFER": offered,
                "REJECTED": rejected
            }
        }
    # =========================
    # Analytics
    # =========================
    @staticmethod
    def get_analytics(user_id):
        # -------------------------
        # Status Counts (Replaces .all() and separate count queries)
        # -------------------------
        status_counts = db.session.query(
            JobApplication.status,
            db.func.count(JobApplication.id)
        ).filter(
            JobApplication.user_id == user_id
        ).group_by(
            JobApplication.status
        ).all()

        by_status = {status.value: 0 for status in ApplicationStatus}
        total_applications = 0
        interviews = 0

        for status, count in status_counts:
            by_status[status.value] = count
            total_applications += count
            if status == ApplicationStatus.INTERVIEW:
                interviews = count

        # -------------------------
        # Response Rate
        # -------------------------
        response_rate = (
            round((interviews / total_applications) * 100, 2)
            if total_applications > 0
            else 0
        )

        # -------------------------
        # Time-in-Stage
        # -------------------------
        time_in_stage = {
            status.value: 0
            for status in ApplicationStatus
        }

        stage_results = db.session.query(
            JobApplication.status,
            db.func.avg(
                db.func.extract(
                    "epoch",
                    JobApplication.updated_at
                    - db.func.cast(
                        JobApplication.applied_date,
                        db.DateTime
                    )
                ) / 86400
            )
        ).filter(
            JobApplication.user_id == user_id
        ).group_by(
            JobApplication.status
        ).all()

        for status, average_days in stage_results:
            if average_days is not None:
                time_in_stage[status.value] = round(float(average_days), 2)

        # -------------------------
        # Best Day of Week
        # -------------------------
        dow_stats = db.session.query(
            db.func.extract('dow', JobApplication.applied_date).label('dow'),
            db.func.count(JobApplication.id).label('total_apps'),
            db.func.sum(
                db.case(
                    (JobApplication.status.in_([
                        ApplicationStatus.INTERVIEW,
                        ApplicationStatus.OFFER
                    ]), 1),
                    else_=0
                )
            ).label('successful_apps')
        ).filter(
            JobApplication.user_id == user_id
        ).group_by(
            db.func.extract('dow', JobApplication.applied_date)
        ).all()

        best_day_index = None
        best_rate = -1

        for row_dow, total_apps, successful_apps in dow_stats:
            if total_apps > 0:
                successful_count = float(successful_apps or 0)
                rate = (successful_count / float(total_apps)) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_day_index = int(row_dow)

        days_map = {
            0: "Sunday",
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday"
        }

        best_day_name = days_map.get(best_day_index) if best_day_index is not None else None

        best_day_of_week = {
            "day": best_day_name,
            "success_rate": round(best_rate, 2) if best_rate >= 0 else 0
        }

        return {
            "total_applications": total_applications,
            "response_rate": response_rate,
            "time_in_stage": time_in_stage,
            "best_day_of_week": best_day_of_week,
            "by_status": by_status
        }
