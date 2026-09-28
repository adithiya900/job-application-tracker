from datetime import datetime, timedelta

from models.job import ApplicationStatus, JobApplication
from services.email_service import send_template_email


def send_interview_reminders(now=None):
    now = now or datetime.utcnow()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)

    applications = JobApplication.query.filter(
        JobApplication.status == ApplicationStatus.INTERVIEW,
        JobApplication.interview_at >= window_start,
        JobApplication.interview_at <= window_end,
        JobApplication.interview_reminder_sent_at.is_(None)
    ).all()

    sent_count = 0
    for application in applications:
        if not application.user or not application.user.email:
            continue

        sent = send_template_email(
            subject=f"Interview reminder: {application.company}",
            recipients=[application.user.email],
            template_name="emails/interview_reminder.html",
            template_context={"application": application},
            body=(
                f"Reminder: your interview for {application.role} at "
                f"{application.company} is scheduled for "
                f"{application.interview_at.isoformat()}."
            )
        )

        if sent:
            application.interview_reminder_sent_at = now
            sent_count += 1

    return sent_count
