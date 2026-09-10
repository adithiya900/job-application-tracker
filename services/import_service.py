import csv
from io import StringIO
from datetime import datetime, date

from extensions import db
from models.job import JobApplication, ApplicationStatus


class ImportService:

    APPLICATION_HEADERS = [
        "company",
        "role",
        "status",
        "applied_date",
        "interview_at",
        "notes"
    ]
    STATUS_UPDATE_HEADERS = ["id", "status"]

    @staticmethod
    def import_applications(file, user_id):

        content = file.read().decode("utf-8-sig")

        reader = csv.DictReader(
            StringIO(content)
        )

        if not reader.fieldnames:
            raise ValueError(
                "CSV file is empty or has no headers"
            )

        headers = [header.strip() for header in reader.fieldnames if header]
        if len(headers) != len(set(headers)):
            raise ValueError("CSV headers must be unique")

        full_import = all(
            header in headers
            for header in ImportService.APPLICATION_HEADERS
        )
        status_update = all(
            header in headers
            for header in ImportService.STATUS_UPDATE_HEADERS
        ) and not full_import

        if not full_import and not status_update:
            required_headers = (
                ImportService.STATUS_UPDATE_HEADERS
                if "id" in headers and "company" not in headers
                else ImportService.APPLICATION_HEADERS
            )
            missing_headers = [
                header for header in required_headers if header not in headers
            ]
            raise ValueError(
                "Missing required headers: "
                + ", ".join(missing_headers)
            )

        imported = 0
        failed = 0
        errors = []

        for row_number, source_row in enumerate(
            reader,
            start=2
        ):
            try:
                row = {
                    headers[index]: value
                    for index, value in enumerate(source_row.values())
                    if index < len(headers)
                }

                if status_update:
                    application_id_value = (row.get("id") or "").strip()
                    if not application_id_value.isdigit():
                        raise ValueError("Application ID must be a positive integer")

                    application_id = int(application_id_value)
                    if application_id < 1:
                        raise ValueError("Application ID must be a positive integer")

                    application = JobApplication.query.filter_by(
                        id=application_id,
                        user_id=user_id
                    ).first()
                    if not application:
                        raise ValueError(
                            f"Application ID {application_id} not found for current user"
                        )

                    status_value = (row.get("status") or "").strip().upper()
                    if status_value not in [status.value for status in ApplicationStatus]:
                        raise ValueError(f"Invalid status: {status_value}")

                    application.status = ApplicationStatus(status_value)
                    imported += 1
                    continue

                company = (
                    row.get("company") or ""
                ).strip()

                role = (
                    row.get("role") or ""
                ).strip()

                status_value = (
                    row.get("status") or ""
                ).strip().upper()

                applied_date_value = (
                    row.get("applied_date") or ""
                ).strip()

                interview_at_value = (
                    row.get("interview_at") or ""
                ).strip()

                notes = (
                    row.get("notes") or ""
                ).strip()

                if not company:
                    raise ValueError(
                        "Company is required"
                    )

                if not role:
                    raise ValueError(
                        "Role is required"
                    )

                if status_value not in [
                    status.value
                    for status in ApplicationStatus
                ]:
                    raise ValueError(
                        f"Invalid status: {status_value}"
                    )

                if applied_date_value:
                    applied_date = datetime.strptime(
                        applied_date_value,
                        "%Y-%m-%d"
                    ).date()
                else:
                    applied_date = date.today()

                if applied_date > date.today():
                    raise ValueError(
                        "Applied date cannot be in the future"
                    )

                interview_at = None

                if interview_at_value:
                    interview_at = datetime.fromisoformat(
                        interview_at_value
                    )

                application_id_value = (row.get("id") or "").strip()
                if application_id_value:
                    if not application_id_value.isdigit():
                        raise ValueError("Application ID must be a positive integer")
                    application = JobApplication.query.filter_by(
                        id=int(application_id_value),
                        user_id=user_id
                    ).first()
                    if not application:
                        raise ValueError(
                            f"Application ID {application_id_value} not found for current user"
                        )
                    application.company = company
                    application.role = role
                    application.status = ApplicationStatus(status_value)
                    application.applied_date = applied_date
                    application.interview_at = interview_at
                    application.notes = notes or None
                else:
                    existing_application = JobApplication.query.filter_by(
                        company=company,
                        role=role,
                        user_id=user_id
                    ).first()
                    if existing_application:
                        raise ValueError("Application already exists")

                    db.session.add(JobApplication(
                        company=company,
                        role=role,
                        status=ApplicationStatus(status_value),
                        applied_date=applied_date,
                        interview_at=interview_at,
                        notes=notes or None,
                        user_id=user_id
                    ))

                imported += 1

            except Exception as e:

                failed += 1

                errors.append({
                    "row": row_number,
                    "error": str(e),
                    "data": row if "row" in locals() else {}
                })

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {
            "imported": imported,
            "failed": failed,
            "errors": errors
        }
