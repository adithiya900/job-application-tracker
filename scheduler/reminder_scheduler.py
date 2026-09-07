import os

from apscheduler.schedulers.background import BackgroundScheduler

from models.user import User
from services.digest_service import send_weekly_digest
from services.reminder_service import send_interview_reminders


def start_scheduler(app):
    if app.testing:
        return None

    if not app.config.get("SCHEDULER_ENABLED", True):
        return None

    if app.debug and os.getenv("WERKZEUG_RUN_MAIN") != "true":
        return None

    existing_scheduler = app.extensions.get("interview_scheduler")
    if existing_scheduler:
        return existing_scheduler

    scheduler = BackgroundScheduler(timezone="UTC")

    def run_reminders():
        with app.app_context():
            send_interview_reminders()

    def run_weekly_digest():
        with app.app_context():
            for user in User.query.all():
                send_weekly_digest(user.id)

    scheduler.add_job(
        run_reminders,
        trigger="interval",
        hours=1,
        id="interview-reminders",
        replace_existing=True
    )
    scheduler.add_job(
        run_weekly_digest,
        trigger="cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly-digest",
        replace_existing=True
    )
    scheduler.start()
    app.extensions["interview_scheduler"] = scheduler
    return scheduler
