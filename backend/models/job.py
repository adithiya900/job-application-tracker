from datetime import date, datetime
from extensions import db
import enum


class ApplicationStatus(enum.Enum):
    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PHONE_SCREEN = "PHONE_SCREEN"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


# Valid status transitions — flexible pipeline
STATUS_TRANSITIONS = {
    ApplicationStatus.APPLIED: [
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.UNDER_REVIEW: [
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.PHONE_SCREEN: [
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.INTERVIEW: [
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.OFFER: [
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.REJECTED: [
        ApplicationStatus.APPLIED,
        ApplicationStatus.UNDER_REVIEW,
    ],
    ApplicationStatus.WITHDRAWN: [
        ApplicationStatus.APPLIED,
    ],
}


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
       default=ApplicationStatus.APPLIED,
       index=True
    )

    # Automatically stores today's date
    applied_date = db.Column(
      db.Date,
      nullable=False,
      default=date.today,
      index=True
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
      db.ForeignKey("users.id", ondelete="CASCADE"),
      nullable=False,
      index=True
    )

    # Relationships
    status_history = db.relationship(
        "ApplicationStatusHistory",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.changed_at"
    )

    interview_details = db.relationship(
        "InterviewDetail",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan",
        uselist=False
    )

    feedback = db.relationship(
        "InterviewFeedback",
        backref="application",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<JobApplication "
            f"{self.company} - {self.role}>"
        )


class ApplicationStatusHistory(db.Model):
    """Records every status change for an application."""
    __tablename__ = "application_status_history"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    old_status = db.Column(
        db.Enum(ApplicationStatus),
        nullable=True   # Null for the initial APPLIED entry
    )

    new_status = db.Column(
        db.Enum(ApplicationStatus),
        nullable=False
    )

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    changed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    notes = db.Column(db.Text, nullable=True)

    changer = db.relationship("User", foreign_keys=[changed_by])

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "old_status": self.old_status.value if self.old_status else None,
            "new_status": self.new_status.value,
            "changed_by": self.changed_by,
            "changed_by_name": self.changer.name if self.changer else None,
            "changed_at": self.changed_at.isoformat(),
            "notes": self.notes,
        }


class InterviewDetail(db.Model):
    """Structured interview scheduling data — stored when HR schedules an interview."""
    __tablename__ = "interview_details"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # one-to-one
        index=True
    )

    interview_date = db.Column(db.Date, nullable=True)
    interview_time = db.Column(db.String(10), nullable=True)   # e.g. "10:30"
    interview_round = db.Column(db.String(100), nullable=True)  # e.g. "Technical Round 1"
    interview_type = db.Column(db.String(50), nullable=True)    # Online / In-person / Phone
    meeting_link = db.Column(db.String(500), nullable=True)
    interviewer = db.Column(db.String(200), nullable=True)
    hr_notes = db.Column(db.Text, nullable=True)  # Internal HR notes — NOT exposed to candidates

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self, include_hr_notes=False):
        data = {
            "id": self.id,
            "application_id": self.application_id,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "interview_time": self.interview_time,
            "interview_round": self.interview_round,
            "interview_type": self.interview_type,
            "meeting_link": self.meeting_link,
            "interviewer": self.interviewer,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_hr_notes:
            data["hr_notes"] = self.hr_notes
        return data


class InterviewFeedback(db.Model):
    """HR/interviewer feedback for a completed interview."""
    __tablename__ = "interview_feedback"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    submitted_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    technical_skills = db.Column(db.String(50), nullable=True)   # e.g. "Excellent", "Good"
    communication = db.Column(db.String(50), nullable=True)
    overall_feedback = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.String(50), nullable=True)   # Hire / No Hire / Maybe
    internal_notes = db.Column(db.Text, nullable=True)   # NOT exposed to candidates

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    submitter = db.relationship("User", foreign_keys=[submitted_by])

    def to_dict(self, include_internal=False):
        data = {
            "id": self.id,
            "application_id": self.application_id,
            "submitted_by": self.submitted_by,
            "submitted_by_name": self.submitter.name if self.submitter else None,
            "technical_skills": self.technical_skills,
            "communication": self.communication,
            "overall_feedback": self.overall_feedback,
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat(),
        }
        if include_internal:
            data["internal_notes"] = self.internal_notes
        return data
