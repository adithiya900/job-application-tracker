from datetime import datetime, timedelta
import zoneinfo

from models.job import ApplicationStatus, JobApplication, InterviewDetail
from models.reminder import FollowUpReminder, ReminderStatus, ReminderType
from services.email_service import send_template_email, send_email
from services.notification_service import publish_notification


def send_interview_reminders(now=None):
    """Send reminders for upcoming interview rounds (based on InterviewDetail records)."""
    now = now or datetime.utcnow()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)

    interviews = InterviewDetail.query.filter(
        InterviewDetail.interview_date >= window_start.date(),
        InterviewDetail.interview_date <= window_end.date()
    ).all()

    sent_count = 0
    for interview in interviews:
        application = interview.application
        if not application or not application.user or not application.user.email:
            continue

        # Build scheduled_at from date + time
        if interview.interview_date and interview.interview_time:
            date_obj = interview.interview_date
            time_str = interview.interview_time or "09:00"
            try:
                hour, minute = [int(x) for x in time_str.split(":")]
                scheduled_at = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)
            except Exception:
                continue

            # Check if within the reminder window
            if not (window_start <= scheduled_at <= window_end):
                continue

        if application.interview_reminder_sent_at is not None:
            continue

        user_tz = application.user.timezone or 'UTC'
        try:
            tz = zoneinfo.ZoneInfo(user_tz)
            interview_time_local = scheduled_at.replace(tzinfo=zoneinfo.ZoneInfo('UTC')).astimezone(tz)
            interview_time_formatted = interview_time_local.strftime('%Y-%m-%d %H:%M %Z')
        except Exception:
            interview_time_formatted = scheduled_at.isoformat() + ' UTC'

        sent = send_template_email(
            subject=f"Interview reminder: {application.company}",
            recipients=[application.user.email],
            template_name="emails/interview_reminder.html",
            template_context={
                "application": application,
                "interview": interview.to_dict(),
                "interview_time_formatted": interview_time_formatted,
            },
            body=(
                f"Reminder: your interview for {application.role} at "
                f"{application.company} is scheduled for "
                f"{interview_time_formatted}.\n\n"
                f"Round: {interview.interview_round or 'N/A'}\n"
                f"Type: {interview.interview_type or 'N/A'}\n"
                f"Meeting: {interview.meeting_link or 'TBD'}\n"
                f"Interviewer: {interview.interviewer or 'TBD'}\n\n"
                f"Job Application Tracker"
            )
        )

        if sent:
            publish_notification(
                user_id=application.user_id,
                notification_type="INTERVIEW_REMINDER",
                message=f"Interview reminder: {application.role} at {application.company}",
                data={
                    "application_id": application.id,
                    "company": application.company,
                    "role": application.role,
                    "interview_date": interview.interview_date.isoformat() if interview.interview_date else None,
                    "interview_time": interview.interview_time,
                    "interview_round": interview.interview_round,
                    "meeting_link": interview.meeting_link,
                    "interviewer": interview.interviewer,
                }
            )
            application.interview_reminder_sent_at = now
            application.interview_at = scheduled_at  # keep backward compat
            sent_count += 1

    return sent_count


def send_follow_up_reminders(now=None):
    """Send scheduled follow-up reminders that are due."""
    now = now or datetime.utcnow()

    due_reminders = FollowUpReminder.query.filter(
        FollowUpReminder.scheduled_at <= now,
        FollowUpReminder.status == ReminderStatus.PENDING,
        FollowUpReminder.dismissed == False,
    ).all()

    sent_count = 0
    for reminder in due_reminders:
        application = reminder.application
        user = application.user if application else None

        if not user or not user.email:
            reminder.status = ReminderStatus.FAILED
            continue

        # Calculate actual send time with lead_time
        send_at = reminder.scheduled_at
        if reminder.lead_time_minutes and reminder.lead_time_minutes > 0:
            from datetime import timedelta
            send_at = reminder.scheduled_at - timedelta(minutes=reminder.lead_time_minutes)
            if now < send_at:
                continue  # Not yet due

        message = reminder.message or "This is a follow-up reminder from HR."
        subject = f"Follow-up Reminder: {application.role} at {application.company}"

        sent = send_email(
            subject=subject,
            recipients=[user.email],
            body=message + "\n\nJob Application Tracker",
        )

        if sent:
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = now
            publish_notification(
                user_id=user.id,
                notification_type="REMINDER_DUE",
                message=reminder.message or "You have a follow-up reminder.",
                data={
                    "reminder_id": reminder.id,
                    "application_id": application.id,
                    "company": application.company,
                    "role": application.role,
                }
            )
            sent_count += 1
        else:
            reminder.status = ReminderStatus.FAILED

    return sent_count
