import logging

from extensions import db
from models.job import JobApplication, ApplicationStatus
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)


# Logger setup
logger = logging.getLogger(__name__)


class ApplicationService:

    @staticmethod
    def create_application(data):

        logger.info(
            "Creating application for company: %s",
            data.get("company")
        )

        # Check for duplicate application
        existing_application = JobApplication.query.filter_by(
            company=data["company"],
            role=data["role"],
            user_id=data["user_id"]
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
            status=data.get("status", ApplicationStatus.APPLIED),
            notes=data.get("notes"),
            user_id=data["user_id"]
        )

        db.session.add(new_application)
        db.session.commit()

        logger.info(
            "Application created successfully with ID: %s",
            new_application.id
        )

        return new_application


    @staticmethod
    def get_all_applications():

        logger.info("Fetching all job applications")

        applications = JobApplication.query.all()

        logger.info(
            "Fetched %s job applications",
            len(applications)
        )

        return applications


    @staticmethod
    def get_application_by_id(application_id):

        logger.info(
            "Fetching application with ID: %s",
            application_id
        )

        application = db.session.get(
            JobApplication,
            application_id
        )

        if not application:

            logger.warning(
                "Application not found with ID: %s",
                application_id
            )

            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        return application


    @staticmethod
    def update_application(application_id, data):

        logger.info(
            "Updating application with ID: %s",
            application_id
        )

        application = db.session.get(
            JobApplication,
            application_id
        )

        if not application:

            logger.warning(
                "Update failed. Application not found: %s",
                application_id
            )

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


    @staticmethod
    def delete_application(application_id):

        logger.info(
            "Deleting application with ID: %s",
            application_id
        )

        application = db.session.get(
            JobApplication,
            application_id
        )

        if not application:

            logger.warning(
                "Delete failed. Application not found: %s",
                application_id
            )

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