import csv
from io import StringIO

from models.job import JobApplication


class ExportService:

    ERROR_HEADERS = ["row", "error", "id", "company", "role", "status", "applied_date", "interview_at", "notes"]

    @staticmethod
    def export_applications(user_id):
        applications = JobApplication.query.filter_by(
            user_id=user_id
        ).order_by(
            JobApplication.applied_date.desc()
        ).all()

        output = StringIO()

        writer = csv.writer(output)

        writer.writerow([
            "id",
            "company",
            "role",
            "status",
            "applied_date",
            "interview_at",
            "notes"
        ])

        for application in applications:

            writer.writerow([
                application.id,
                application.company,
                application.role,
                application.status.value,
                (
                    application.applied_date.isoformat()
                    if application.applied_date
                    else ""
                ),
                (
                    application.interview_at.isoformat()
                    if application.interview_at
                    else ""
                ),
                application.notes or ""
            ])

        output.seek(0)

        return output

    @staticmethod
    def export_error_log(errors):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(ExportService.ERROR_HEADERS)

        for failure in errors:
            row = failure.get("data", {})
            writer.writerow([
                failure.get("row", ""),
                failure.get("error", ""),
                row.get("id", ""),
                row.get("company", ""),
                row.get("role", ""),
                row.get("status", ""),
                row.get("applied_date", ""),
                row.get("interview_at", ""),
                row.get("notes", "")
            ])

        output.seek(0)
        return output