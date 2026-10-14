from extensions import db
from datetime import datetime
import enum


class ReminderType(enum.Enum):
    PHONE_CALL = "PHONE_CALL"
    INTERVIEW = "INTERVIEW"
    FOLLOW_UP = "FOLLOW_UP"
    CUSTOM = "CUSTOM"


class ReminderStatus(enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DISMISSED = "DISMISSED"


class FollowUpReminder(db.Model):
    """
    A reminder for an application, either HR-scheduled or candidate-scheduled.
    Can be triggered by the scheduler via APScheduler.

    One application can have many reminders.
    """
    __tablename__ = "follow_up_reminders"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # User who created / owns the reminder (the candidate)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # HR who created the reminder (optional, null if candidate-created)
    created_by_hr_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    reminder_type = db.Column(
        db.Enum(ReminderType),
        nullable=False,
        default=ReminderType.FOLLOW_UP
    )

    message = db.Column(db.Text, nullable=True)

    scheduled_at = db.Column(db.DateTime, nullable=False)

    # How many minutes before/after scheduled_at to send (default: send at scheduled time)
    lead_time_minutes = db.Column(db.Integer, nullable=True, default=0)

    status = db.Column(
        db.Enum(ReminderStatus),
        nullable=False,
        default=ReminderStatus.PENDING,
        index=True
    )

    sent_at = db.Column(db.DateTime, nullable=True)

    dismissed = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = db.relationship("JobApplication", backref="reminders")
    owner = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "user_id": self.user_id,
            "created_by_hr_id": self.created_by_hr_id,
            "reminder_type": self.reminder_type.value if self.reminder_type else None,
            "message": self.message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "lead_time_minutes": self.lead_time_minutes,
            "status": self.status.value if self.status else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "dismissed": self.dismissed,
            "created_at": self.created_at.isoformat(),
        }
