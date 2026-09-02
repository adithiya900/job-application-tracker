from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)

from datetime import date


VALID_STATUSES = [
    "APPLIED",
    "PHONE_SCREEN",
    "INTERVIEW",
    "OFFER",
    "REJECTED"
]


# ==========================================
# Create Application Schema
# ==========================================

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
        validate=validate.OneOf(VALID_STATUSES)
    )

    notes = fields.Str(
        required=False,
        allow_none=True
    )

    applied_date = fields.Date(
        required=False
    )

    @validates("company")
    def validate_company(self, value, **kwargs):

        if not value.strip():
            raise ValidationError(
                "Company cannot be empty"
            )

    @validates("role")
    def validate_role(self, value, **kwargs):

        if not value.strip():
            raise ValidationError(
                "Role cannot be empty"
            )

    @validates("applied_date")
    def validate_applied_date(self, value, **kwargs):

        if value > date.today():

            raise ValidationError(
                "Applied date cannot be in the future"
            )


# ==========================================
# Update Application Schema
# ==========================================

class UpdateApplicationSchema(Schema):

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

    @validates("company")
    def validate_company(self, value, **kwargs):

        if not value.strip():

            raise ValidationError(
                "Company cannot be empty"
            )

    @validates("role")
    def validate_role(self, value, **kwargs):

        if not value.strip():

            raise ValidationError(
                "Role cannot be empty"
            )

    @validates("applied_date")
    def validate_applied_date(self, value, **kwargs):

        if value > date.today():

            raise ValidationError(
                "Applied date cannot be in the future"
            )