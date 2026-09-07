from datetime import datetime, time, timedelta

from models.job import JobApplication
from models.user import User
from services.email_service import send_template_email


def send_weekly_digest(user_id, now=None):
    now = now or datetime.utcnow()
    week_start = now.date() - timedelta(days=now.weekday())
    week_start_at = datetime.combine(week_start, time.min)

    user = User.query.get(user_id)
    if not user or not user.email:
        return False

    applications = JobApplication.query.filter(
        JobApplication.user_id == user_id,
        JobApplication.updated_at >= week_start_at,
        JobApplication.updated_at <= now
    ).order_by(JobApplication.updated_at.desc()).all()

    context = {
        "user": user,
        "applications": applications,
        "week_start": week_start,
        "week_end": now.date()
    }

    body_lines = [
        f"Hello {user.name},",
        "",
        f"Here are your job applications updated since {week_start.isoformat()}:",
        ""
    ]

    if applications:
        body_lines.extend(
            f"- {application.company} | {application.role} | "
            f"{application.status.value}"
            for application in applications
        )
    else:
        body_lines.append("No applications were updated this week.")

    body_lines.extend(["", "Job Application Tracker"])

    return send_template_email(
        subject="Your weekly job application digest",
        recipients=[user.email],
        template_name="emails/weekly_digest.html",
        template_context=context,
        body="\n".join(body_lines)
    )
