from extensions import db
from models.job import JobApplication, ApplicationStatus
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)


class ApplicationService:

    @staticmethod
    def create_application(data):

        # Check for duplicate application
        existing_application = JobApplication.query.filter_by(
            company=data["company"],
            role=data["role"],
            user_id=data["user_id"]
        ).first()

        if existing_application:
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

        return new_application


    @staticmethod
    def get_all_applications():
        return JobApplication.query.all()


    @staticmethod
    def get_application_by_id(application_id):

        application = db.session.get(
            JobApplication,
            application_id
        )

        if not application:
            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        return application


    @staticmethod
    def update_application(application_id, data):

        application = db.session.get(
            JobApplication,
            application_id
        )

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

        return application


    @staticmethod
    def delete_application(application_id):

        application = db.session.get(
            JobApplication,
            application_id
        )

        if not application:
            raise ApplicationNotFound(
                f"Application with ID {application_id} not found."
            )

        db.session.delete(application)
        db.session.commit()

        return True