from datetime import date, datetime
from extensions import db
import enum


class ApplicationStatus(enum.Enum):
    APPLIED = "APPLIED"
    PHONE_SCREEN = "PHONE_SCREEN"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"


class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(100),
        nullable=False
    )

    status = db.Column(
        db.Enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.APPLIED
    )

    # Automatically stores today's date
    applied_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    interview_at = db.Column(
        db.DateTime,
        nullable=True
    )

    interview_reminder_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    # =========================
    # Resume File Path
    # =========================
    resume_path = db.Column(
        db.String(255),
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<JobApplication "
            f"{self.company} - {self.role}>"
        )