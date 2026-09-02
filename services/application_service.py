import logging

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

        # Check duplicate application
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

        # Create new application
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
    # Search + Filter + Sorting + Pagination
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

        # Logged-in user's applications only
        query = JobApplication.query.filter_by(
            user_id=user_id
        )

        # =========================
        # Search by Company or Role
        # =========================
        if search:

            search_term = f"%{search}%"

            query = query.filter(
                db.or_(
                    JobApplication.company.ilike(search_term),
                    JobApplication.role.ilike(search_term)
                )
            )

        # =========================
        # Filter by Status
        # =========================
        if status:

            query = query.filter(
                JobApplication.status == status
            )

        # =========================
        # Sorting
        # =========================
        if sort == "oldest":

            query = query.order_by(
                JobApplication.applied_date.asc()
            )

        elif sort == "company":

            query = query.order_by(
                JobApplication.company.asc()
            )

        else:

            # Default: newest first
            query = query.order_by(
                JobApplication.applied_date.desc()
            )

        # =========================
        # Pagination
        # =========================
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        logger.info(
            "Page %s contains %s applications",
            page,
            len(pagination.items)
        )

        return pagination


    # =========================
    # Get Application By ID
    # =========================
    @staticmethod
    def get_application_by_id(application_id, user_id):

        logger.info(
            "Fetching application ID: %s for user ID: %s",
            application_id,
            user_id
        )

        application = JobApplication.query.filter_by(
            id=application_id,
            user_id=user_id
        ).first()

        if not application:

            logger.warning(
                "Application not found: %s",
                application_id
            )

            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        return application


    # =========================
    # Update Application
    # =========================
    @staticmethod
    def update_application(application_id, data, user_id):

        logger.info(
            "Updating application ID: %s",
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

        db.session.commit()

        logger.info(
            "Application updated successfully: %s",
            application_id
        )

        return application


    # =========================
    # Delete Application
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

        db.session.delete(application)
        db.session.commit()

        logger.info(
            "Application deleted successfully: %s",
            application_id
        )

        return True


    # =========================
    # Dashboard Statistics
    # =========================
    @staticmethod
    def get_dashboard_statistics(user_id):

        logger.info(
            "Fetching dashboard statistics for user ID: %s",
            user_id
        )

        # Get logged-in user's applications
        applications = JobApplication.query.filter_by(
            user_id=user_id
        ).all()

        # Total
        total_applications = len(applications)

        # Applied
        applied = sum(
            1 for application in applications
            if application.status == ApplicationStatus.APPLIED
        )

        # Interview
        interview = sum(
            1 for application in applications
            if application.status == ApplicationStatus.INTERVIEW
        )

        # Rejected
        rejected = sum(
            1 for application in applications
            if application.status == ApplicationStatus.REJECTED
        )

        # Offer
        offered = sum(
            1 for application in applications
            if application.status == ApplicationStatus.OFFER
        )

        return {
            "total_applications": total_applications,
            "applied": applied,
            "interview": interview,
            "rejected": rejected,
            "offered": offered
        }