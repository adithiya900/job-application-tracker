from app import app
from scheduler.reminder_scheduler import start_scheduler

if __name__ == "__main__":
    scheduler = start_scheduler(app)

    if scheduler is None:
        raise RuntimeError(
            "Scheduler did not start. Check SCHEDULER_ENABLED."
        )

    scheduler.print_jobs()

    try:
        scheduler._thread.join()
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
