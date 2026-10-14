from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)
from datetime import date

# Single source of truth for valid statuses
VALID_STATUSES = [
    "APPLIED",
    "UNDER_REVIEW",
    "PHONE_CALL",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
]

# Statuses that HR can set (candidates cannot directly set HR-only statuses)
HR_VALID_STATUSES = [
    "APPLIED",
    "UNDER_REVIEW",
    "PHONE_CALL",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
]

# Statuses candidates can set when creating (only APPLIED makes sense)
CANDIDATE_CREATE_STATUSES = ["APPLIED"]

# Interview round types
ROUND_TYPES = ["Phone Screen", "Technical", "HR", "Managerial", "Final", "Other"]
INTERVIEW_TYPES = ["Online", "In-person", "Phone"]


class CreateApplicationSchema(Schema):

    company = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={
            "required": "Company is required"
        }
    )

    role = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={
            "required": "Role is required"
        }
    )

    status = fields.Str(
        required=False,
        validate=validate.OneOf(CANDIDATE_CREATE_STATUSES)
    )

    notes = fields.Str(
        required=False,
        allow_none=True
    )

    applied_date = fields.Date(
        required=False
    )

    interview_at = fields.DateTime(
        required=False,
        allow_none=True
    )

    tags = fields.List(
        fields.Str(validate=validate.Length(min=1, max=30)),
        required=False,
        allow_none=True
    )

    @validates("company")
    def validate_company(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Company cannot be empty")

    @validates("role")
    def validate_role(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Role cannot be empty")

    @validates("applied_date")
    def validate_applied_date(self, value, **kwargs):
        if value > date.today():
            raise ValidationError(
                "Applied date cannot be in the future"
            )


class UpdateApplicationSchema(Schema):
    """Used by candidates to update their own applications (not status)."""

    company = fields.Str(
        required=False,
        validate=validate.Length(min=1)
    )

    role = fields.Str(
        required=False,
        validate=validate.Length(min=1)
    )

    status = fields.Str(
        required=False,
        validate=validate.OneOf(VALID_STATUSES)
    )

    notes = fields.Str(
        required=False,
        allow_none=True
    )

    applied_date = fields.Date(
        required=False
    )

    interview_at = fields.DateTime(
        required=False,
        allow_none=True
    )

    tags = fields.List(
        fields.Str(validate=validate.Length(min=1, max=30)),
        required=False,
        allow_none=True
    )

    @validates("company")
    def validate_company(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Company cannot be empty")

    @validates("role")
    def validate_role(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Role cannot be empty")

    @validates("applied_date")
    def validate_applied_date(self, value, **kwargs):
        if value > date.today():
            raise ValidationError(
                "Applied date cannot be in the future"
            )


class HRStatusUpdateSchema(Schema):
    """Used by HR to update application status."""

    status = fields.Str(
        required=True,
        validate=validate.OneOf(HR_VALID_STATUSES),
        error_messages={"required": "Status is required"}
    )

    notes = fields.Str(
        required=False,
        allow_none=True
    )

    # Allow setting shortlist alongside status update
    is_shortlisted = fields.Bool(required=False, allow_none=True)


class HRInterviewSchema(Schema):
    """Used by HR to schedule or update interview details."""

    interview_date = fields.Date(required=False, allow_none=True)
    interview_time = fields.Str(required=False, allow_none=True)
    interview_round = fields.Str(required=False, allow_none=True)
    round_type = fields.Str(required=False, allow_none=True)
    interview_type = fields.Str(required=False, allow_none=True)
    meeting_link = fields.Str(required=False, allow_none=True)
    interviewer = fields.Str(required=False, allow_none=True)
    hr_notes = fields.Str(required=False, allow_none=True)


class HRFeedbackSchema(Schema):
    """Used by HR/interviewer to submit interview feedback."""

    technical_skills = fields.Str(required=False, allow_none=True)
    communication = fields.Str(required=False, allow_none=True)
    rating = fields.Int(required=False, allow_none=True, validate=validate.Range(min=1, max=5))
    strengths = fields.Str(required=False, allow_none=True)
    weaknesses = fields.Str(required=False, allow_none=True)
    candidate_facing = fields.Bool(required=False, allow_none=True)
    candidate_facing_summary = fields.Str(required=False, allow_none=True)
    overall_feedback = fields.Str(required=False, allow_none=True)
    recommendation = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["Hire", "No Hire", "Maybe", None])
    )
    internal_notes = fields.Str(required=False, allow_none=True)


class ReminderSchema(Schema):
    """Used for creating and updating follow-up reminders."""

    application_id = fields.Int(required=True)
    reminder_type = fields.Str(
        required=False,
        validate=validate.OneOf(["PHONE_CALL", "INTERVIEW", "FOLLOW_UP", "CUSTOM"])
    )
    message = fields.Str(required=False, allow_none=True)
    scheduled_at = fields.DateTime(required=True)
    lead_time_minutes = fields.Int(required=False, allow_none=True)