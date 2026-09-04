import logging
import os

from extensions import db
from models.job import JobApplication, ApplicationStatus
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)


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
            notes=data.get("notes"),
            user_id=user_id
        )

        db.session.add(new_application)
        db.session.commit()

        logger.info(
            "Application created successfully with ID: %s",
            new_application.id
        )

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

        application.notes = data.get(
            "notes",
            application.notes
        )

        if "applied_date" in data:
            application.applied_date = data["applied_date"]

        db.session.commit()

        logger.info(
            "Application updated successfully: %s",
            application_id
        )

        return application


    # =========================
    # Delete Application
    # Delete Resume File (Cascade)
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
        # Delete Application from Database
        # =========================
        db.session.delete(application)

        db.session.commit()

        logger.info(
            "Application and resume deleted successfully: %s",
            application_id
        )

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
            1 for application in applications
            if application.status == ApplicationStatus.APPLIED
        )

        phone_screen = sum(
            1 for application in applications
            if application.status == ApplicationStatus.PHONE_SCREEN
        )

        interview = sum(
            1 for application in applications
            if application.status == ApplicationStatus.INTERVIEW
        )

        rejected = sum(
            1 for application in applications
            if application.status == ApplicationStatus.REJECTED
        )

        offered = sum(
            1 for application in applications
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