from datetime import datetime, timedelta
import zoneinfo

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

        # Format interview time in user's timezone
        interview_time_utc = application.interview_at
        user_tz = application.user.timezone or 'UTC'
        try:
            tz = zoneinfo.ZoneInfo(user_tz)
            interview_time_local = interview_time_utc.replace(tzinfo=zoneinfo.ZoneInfo('UTC')).astimezone(tz)
            interview_time_formatted = interview_time_local.strftime('%Y-%m-%d %H:%M %Z')
        except Exception:
            # Fallback to UTC if timezone is invalid
            interview_time_formatted = interview_time_utc.isoformat() + ' UTC'

        sent = send_template_email(
            subject=f"Interview reminder: {application.company}",
            recipients=[application.user.email],
            template_name="emails/interview_reminder.html",
            template_context={"application": application, "interview_time_formatted": interview_time_formatted},
            body=(
                f"Reminder: your interview for {application.role} at "
                f"{application.company} is scheduled for "
                f"{interview_time_formatted}."
            )
        )

        if sent:
            application.interview_reminder_sent_at = now
            sent_count += 1

    return sent_count
