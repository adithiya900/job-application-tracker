"""
HR API Blueprint
================
Provides endpoints for HR personnel to manage job applications.

All endpoints require HR or ADMIN role.

Routes:
  GET    /api/hr/applications
  GET    /api/hr/applications/<id>
  PATCH  /api/hr/applications/<id>/status
  PATCH  /api/hr/applications/<id>/interview
  POST   /api/hr/applications/<id>/feedback
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime

from extensions import db, cache
from models.job import (
    JobApplication,
    ApplicationStatus,
    ApplicationStatusHistory,
    InterviewDetail,
    InterviewFeedback,
    STATUS_TRANSITIONS,
)
from models.user import User
from utils.admin import hr_required
from schemas.application_schema import (
    HRStatusUpdateSchema,
    HRInterviewSchema,
    HRFeedbackSchema,
)
from services.notification_service import publish_notification
from services.email_service import send_email

hr_bp = Blueprint("hr", __name__, url_prefix="/api/hr")


# ==============================================================
# Shared serializer for HR view of an application
# ==============================================================

def serialize_application_hr(application, include_interview=True):
    """Full serialization including candidate info and interview details."""
    candidate = db.session.get(User, application.user_id)

    data = {
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "applied_date": (
            application.applied_date.isoformat()
            if application.applied_date else None
        ),
        "updated_at": (
            application.updated_at.isoformat()
            if application.updated_at else None
        ),
        "interview_at": (
            application.interview_at.isoformat()
            if application.interview_at else None
        ),
        "notes": application.notes,
        "resume_path": application.resume_path,
        "user_id": application.user_id,
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
        } if candidate else None,
    }

    if include_interview and application.interview_details:
        data["interview_details"] = application.interview_details.to_dict(include_hr_notes=True)
    else:
        data["interview_details"] = None

    return data


def record_status_history(application, old_status, new_status, changed_by_id, notes=None):
    """Create a status history record and commit it."""
    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by_id,
        notes=notes,
    )
    db.session.add(history)


def send_status_notification(application, old_status, new_status):
    """Publish Redis notification and send email to candidate."""
    candidate = db.session.get(User, application.user_id)
    if not candidate:
        return

    status_labels = {
        "APPLIED": "Applied",
        "UNDER_REVIEW": "Under Review",
        "PHONE_SCREEN": "Phone Screen",
        "INTERVIEW": "Interview",
        "OFFER": "Offer",
        "REJECTED": "Rejected",
        "WITHDRAWN": "Withdrawn",
    }

    new_label = status_labels.get(new_status.value, new_status.value)

    message = (
        f"Your application for {application.role} at {application.company} "
        f"has moved to {new_label}."
    )

    # Publish to Redis Pub/Sub → SSE stream
    publish_notification(
        user_id=application.user_id,
        notification_type="APPLICATION_STATUS_CHANGED",
        message=message,
        data={
            "application_id": application.id,
            "company": application.company,
            "role": application.role,
            "old_status": old_status.value if old_status else None,
            "new_status": new_status.value,
        }
    )

    # Send email
    if candidate.email:
        send_email(
            subject=f"Application Update: {application.role} at {application.company}",
            recipients=[candidate.email],
            body=(
                f"Hello {candidate.name},\n\n"
                f"{message}\n\n"
                f"Company: {application.company}\n"
                f"Role: {application.role}\n"
                f"Previous Status: {old_status.value if old_status else 'N/A'}\n"
                f"New Status: {new_status.value}\n\n"
                f"Job Application Tracker"
            )
        )


# ==============================================================
# GET /api/hr/applications
# List all applications visible to HR with filters
# ==============================================================

@hr_bp.route("/applications", methods=["GET"])
@hr_required
def hr_list_applications():
    try:
        search = request.args.get("search")
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        sort = request.args.get("sort", "newest").lower()

        if per_page > 100:
            per_page = 100
        if page < 1:
            page = 1

        # HR sees all applications
        query = JobApplication.query

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    JobApplication.company.ilike(search_term),
                    JobApplication.role.ilike(search_term),
                )
            )

        if status:
            try:
                status_enum = ApplicationStatus[status.upper()]
                query = query.filter(JobApplication.status == status_enum)
            except KeyError:
                return jsonify({"error": "Invalid status"}), 400

        if sort == "oldest":
            query = query.order_by(JobApplication.applied_date.asc())
        elif sort == "company":
            query = query.order_by(JobApplication.company.asc())
        else:
            query = query.order_by(JobApplication.applied_date.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        applications = [
            serialize_application_hr(app, include_interview=False)
            for app in pagination.items
        ]

        # Summary stats for HR dashboard
        total = JobApplication.query.count()
        stats = {}
        for status_val in ApplicationStatus:
            stats[status_val.value] = JobApplication.query.filter_by(
                status=status_val
            ).count()

        return jsonify({
            "applications": applications,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "stats": stats,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/applications/<id>
# Get a single application with full details
# ==============================================================

@hr_bp.route("/applications/<int:application_id>", methods=["GET"])
@hr_required
def hr_get_application(application_id):
    try:
        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        data = serialize_application_hr(application, include_interview=True)

        # Include status history
        data["status_history"] = [
            h.to_dict() for h in application.status_history
        ]

        # Include feedback (with internal notes for HR)
        data["feedback"] = [
            f.to_dict(include_internal=True) for f in application.feedback
        ]

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# PATCH /api/hr/applications/<id>/status
# HR updates application status
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/status", methods=["PATCH"])
@hr_required
def hr_update_status(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        schema = HRStatusUpdateSchema()
        try:
            validated = schema.load(data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        new_status_value = validated["status"]
        notes = validated.get("notes")

        try:
            new_status = ApplicationStatus[new_status_value]
        except KeyError:
            return jsonify({"error": "Invalid status"}), 400

        old_status = application.status

        # Validate transition unless it's a no-op
        if new_status == old_status:
            return jsonify({"message": "Status unchanged", "application": serialize_application_hr(application)}), 200

        allowed_transitions = STATUS_TRANSITIONS.get(old_status, [])
        if new_status not in allowed_transitions:
            return jsonify({
                "error": f"Invalid status transition from {old_status.value} to {new_status.value}",
                "allowed_transitions": [s.value for s in allowed_transitions],
            }), 422

        # Update status
        application.status = new_status

        # Record history
        record_status_history(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by_id=hr_user_id,
            notes=notes,
        )

        db.session.commit()

        # Invalidate analytics cache
        cache.delete(f"analytics:user:{application.user_id}")

        # Notify candidate via Redis/SSE + email
        send_status_notification(application, old_status, new_status)

        return jsonify({
            "message": f"Status updated to {new_status.value}",
            "application": serialize_application_hr(application),
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# PATCH /api/hr/applications/<id>/interview
# HR schedules or updates interview details
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/interview", methods=["PATCH"])
@hr_required
def hr_update_interview(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        schema = HRInterviewSchema()
        try:
            validated = schema.load(data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        # Upsert interview details
        interview = application.interview_details
        if not interview:
            interview = InterviewDetail(application_id=application_id)
            db.session.add(interview)

        if "interview_date" in validated:
            interview.interview_date = validated["interview_date"]
        if "interview_time" in validated:
            interview.interview_time = validated["interview_time"]
        if "interview_round" in validated:
            interview.interview_round = validated["interview_round"]
        if "interview_type" in validated:
            interview.interview_type = validated["interview_type"]
        if "meeting_link" in validated:
            interview.meeting_link = validated["meeting_link"]
        if "interviewer" in validated:
            interview.interviewer = validated["interviewer"]
        if "hr_notes" in validated:
            interview.hr_notes = validated["hr_notes"]

        # Also sync interview_at on the application for backward compat
        if validated.get("interview_date"):
            date_obj = validated["interview_date"]
            time_str = validated.get("interview_time", "00:00") or "00:00"
            try:
                hour, minute = [int(x) for x in time_str.split(":")]
                application.interview_at = datetime(
                    date_obj.year, date_obj.month, date_obj.day, hour, minute
                )
                application.interview_reminder_sent_at = None
            except Exception:
                pass

        db.session.commit()

        # Notify candidate about interview scheduling
        candidate = db.session.get(User, application.user_id)
        if candidate:
            publish_notification(
                user_id=application.user_id,
                notification_type="INTERVIEW_SCHEDULED",
                message=(
                    f"Interview scheduled for {application.role} at {application.company}."
                ),
                data={
                    "application_id": application.id,
                    "interview_date": interview.interview_date.isoformat() if interview.interview_date else None,
                    "interview_time": interview.interview_time,
                    "interview_type": interview.interview_type,
                    "meeting_link": interview.meeting_link,
                }
            )

            if candidate.email:
                send_email(
                    subject=f"Interview Scheduled: {application.role} at {application.company}",
                    recipients=[candidate.email],
                    body=(
                        f"Hello {candidate.name},\n\n"
                        f"An interview has been scheduled for your application.\n\n"
                        f"Company: {application.company}\n"
                        f"Role: {application.role}\n"
                        f"Date: {interview.interview_date}\n"
                        f"Time: {interview.interview_time}\n"
                        f"Type: {interview.interview_type}\n"
                        f"Round: {interview.interview_round}\n"
                        f"Meeting Link: {interview.meeting_link or 'TBD'}\n"
                        f"Interviewer: {interview.interviewer or 'TBD'}\n\n"
                        f"Job Application Tracker"
                    )
                )

        return jsonify({
            "message": "Interview details updated",
            "interview": interview.to_dict(include_hr_notes=True),
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# POST /api/hr/applications/<id>/feedback
# HR/interviewer submits interview feedback
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/feedback", methods=["POST"])
@hr_required
def hr_add_feedback(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        schema = HRFeedbackSchema()
        try:
            validated = schema.load(data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        feedback = InterviewFeedback(
            application_id=application_id,
            submitted_by=hr_user_id,
            technical_skills=validated.get("technical_skills"),
            communication=validated.get("communication"),
            overall_feedback=validated.get("overall_feedback"),
            recommendation=validated.get("recommendation"),
            internal_notes=validated.get("internal_notes"),
        )
        db.session.add(feedback)
        db.session.commit()

        return jsonify({
            "message": "Feedback submitted",
            "feedback": feedback.to_dict(include_internal=True),
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/stats
# HR dashboard summary statistics
# ==============================================================

@hr_bp.route("/stats", methods=["GET"])
@hr_required
def hr_stats():
    try:
        stats = {}
        for status_val in ApplicationStatus:
            stats[status_val.value] = JobApplication.query.filter_by(
                status=status_val
            ).count()

        total = JobApplication.query.count()

        return jsonify({
            "total": total,
            "by_status": stats,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
