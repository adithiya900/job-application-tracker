"""
HR API Blueprint
===============
Provides endpoints for HR personnel to manage job applications.

All endpoints require HR or ADMIN role.

Routes:
  GET    /api/hr/applications
  GET    /api/hr/applications/<id>
  PATCH  /api/hr/applications/<id>/status
  PATCH  /api/hr/applications/<id>/interview
  POST   /api/hr/applications/<id>/feedback
"""

from flask import Blueprint, request, jsonify, send_file
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
from models.user import User, Role
from models.audit_log import AuditLog
from models.reminder import FollowUpReminder, ReminderType, ReminderStatus
from utils.admin import hr_required
from schemas.application_schema import (
    HRStatusUpdateSchema,
    HRInterviewSchema,
    HRFeedbackSchema,
    ReminderSchema,
)
from services.notification_service import (
    publish_admin_notification,
    publish_notification,
    publish_human_resource_notification,
)
from services.email_service import send_email

hr_bp = Blueprint("hr", __name__, url_prefix="/api/hr")


# ==============================================================
# Shared helpers
# ==============================================================

def _get_candidate(application):
    """Return the candidate User object for an application."""
    return db.session.get(User, application.user_id)


def require_candidate_active(application):
    """Return an error response if the candidate account is disabled, else None."""
    candidate = db.session.get(User, application.user_id)
    if not candidate or not candidate.is_active:
        return jsonify({
            "error": "This candidate account is disabled. HR actions are not allowed."
        }), 403
    return None


def require_application_workable(application):
    """
    Return an error response when the application has been withdrawn by the
    candidate, else None.

    A withdrawn application is closed: HR cannot change its status, schedule
    interviews, submit feedback or message the candidate. Enforced here as well
    as in the UI so the rules cannot be bypassed through the API.
    """
    if application.status == ApplicationStatus.WITHDRAWN:
        return jsonify({
            "error": "This application was withdrawn by the candidate. "
                     "No further actions are available."
        }), 403
    return None


# ==============================================================
# Shared serializer for HR view of an application
# ==============================================================

def serialize_application_hr(application, include_interview=True):
    """Full serialization including candidate info and interview details."""
    candidate = _get_candidate(application)

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
        "is_shortlisted": bool(application.is_shortlisted),
        "user_id": application.user_id,
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone_number": candidate.phone_number,
            "is_active": candidate.is_active,
        } if candidate else {
            "id": None,
            "name": None,
            "email": None,
            "is_active": False,
        },
    }

    if include_interview:
        interviews = db.session.query(InterviewDetail).filter_by(application_id=application.id).order_by(InterviewDetail.created_at).all()
        data["interview_details"] = [i.to_dict(include_hr_notes=True) for i in interviews]
    else:
        data["interview_details"] = None

    # Serialize reminders for HR view
    reminders = FollowUpReminder.query.filter_by(application_id=application.id, dismissed=False).order_by(FollowUpReminder.scheduled_at).all()
    data["reminders"] = [r.to_dict() for r in reminders]

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
        "PHONE_CALL": "Phone Call",
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
                    JobApplication.user_id.in_(
                        db.session.query(User.id).filter(
                            db.or_(
                                User.name.ilike(search_term),
                                User.email.ilike(search_term),
                            )
                        )
                    ),
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
# GET /api/hr/applications/<id>/resume
# HR views candidate resume
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/resume", methods=["GET"])
@hr_required
def hr_view_resume(application_id):
    try:
        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        if not application.resume_path:
            return jsonify({"error": "No resume uploaded for this application"}), 404

        import os
        if not os.path.exists(application.resume_path):
            return jsonify({"error": "Resume file not found"}), 404

        return send_file(application.resume_path, as_attachment=True)
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

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        blocked = require_candidate_active(application)
        if blocked is not None:
            return blocked

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
        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="application_status_updated",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "old_status": old_status.value,
                "new_status": new_status.value,
            },
        ))

        db.session.commit()

        # Invalidate analytics cache
        cache.delete(f"analytics:user:{application.user_id}")

        # Notify candidate via Redis/SSE + email
        send_status_notification(application, old_status, new_status)
        publish_admin_notification(
            "APPLICATION_STATUS_CHANGED",
            f"{application.role} at {application.company} moved to {new_status.value}.",
            {
                "application_id": application.id,
                "candidate_id": application.user_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
            },
        )

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

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        blocked = require_candidate_active(application)
        if blocked is not None:
            return blocked

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        schema = HRInterviewSchema()
        try:
            validated = schema.load(data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        interview_type = validated.get("interview_type")
        meeting_link = validated.get("meeting_link")
        if interview_type == "Online":
            link = (meeting_link or "").strip()
            if not link:
                return jsonify({
                    "error": "Meeting link is required for Google Meet interviews."
                }), 400
            validated["meeting_link"] = link
        else:
            validated["meeting_link"] = None

        # Create a new interview detail (supports multiple rounds)
        interview = InterviewDetail(application_id=application_id)
        db.session.add(interview)

        if "interview_date" in validated:
            interview.interview_date = validated["interview_date"]
        if "interview_time" in validated:
            interview.interview_time = validated["interview_time"]
        if "interview_round" in validated:
            interview.interview_round = validated["interview_round"]
        if "round_type" in validated:
            interview.round_type = validated["round_type"]
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

        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="interview_scheduled",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "interview_date": interview.interview_date.isoformat() if interview.interview_date else None,
                "interview_round": interview.interview_round,
            },
        ))
        db.session.commit()
        publish_admin_notification(
            "INTERVIEW_SCHEDULED",
            f"Interview scheduled for {application.role} at {application.company}.",
            {"application_id": application.id, "candidate_id": application.user_id},
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

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        blocked = require_candidate_active(application)
        if blocked is not None:
            return blocked

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
            rating=validated.get("rating"),
            strengths=validated.get("strengths"),
            weaknesses=validated.get("weaknesses"),
            candidate_facing=validated.get("candidate_facing", False),
            candidate_facing_summary=validated.get("candidate_facing_summary"),
            overall_feedback=validated.get("overall_feedback"),
            recommendation=validated.get("recommendation"),
            internal_notes=validated.get("internal_notes"),
        )
        db.session.add(feedback)
        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="interview_feedback_submitted",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "recommendation": validated.get("recommendation"),
            },
        ))
        db.session.commit()
        publish_admin_notification(
            "INTERVIEW_FEEDBACK_SUBMITTED",
            f"Interview feedback submitted for {application.role} at {application.company}.",
            {"application_id": application.id, "candidate_id": application.user_id},
        )

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


# ==============================================================
# POST /api/hr/applications/<id>/notify
# HR sends a message/notification to the candidate
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/notify", methods=["POST"])
@hr_required
def hr_notify_candidate(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        blocked = require_candidate_active(application)
        if blocked is not None:
            return blocked

        data = request.get_json()
        if not data or not data.get("message"):
            return jsonify({"error": "Message is required"}), 400

        message = data["message"]
        notification_type = data.get("type", "HR_MESSAGE")

        publish_notification(
            user_id=application.user_id,
            notification_type=notification_type,
            message=message,
            data={
                "application_id": application.id,
                "candidate_id": application.user_id,
                "company": application.company,
                "role": application.role,
                "sent_by_hr_id": hr_user_id,
            },
        )

        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="message_sent_to_candidate",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "notification_type": notification_type,
            },
        ))
        db.session.commit()

        return jsonify({
            "message": "Notification sent to candidate successfully.",
            "application_id": application.id,
            "candidate_id": application.user_id,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/interviews
# List all interview details across all applications (HR view)
# ==============================================================

@hr_bp.route("/hr/applications", methods=["GET"])
@hr_required
def hr_list_interviews():
    try:
        hr_user_id = int(get_jwt_identity())

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        if per_page > 100:
            per_page = 100
        if page < 1:
            page = 1

        status_filter = request.args.get("status")
        search = request.args.get("search")

        query = (
            db.session.query(InterviewDetail)
            .join(JobApplication, InterviewDetail.application_id == JobApplication.id)
        )

        if status_filter:
            query = query.filter(InterviewDetail.round_type == status_filter)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    JobApplication.company.ilike(search_term),
                    JobApplication.role.ilike(search_term),
                )
            )

        query = query.order_by(InterviewDetail.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        result = []
        for detail in pagination.items:
            app = detail.application
            candidate = db.session.get(User, app.user_id)
            result.append({
                "id": detail.id,
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "candidate_name": candidate.name if candidate else None,
                "candidate_email": candidate.email if candidate else None,
                "candidate_id": application.user_id,
                "interview_date": detail.interview_date.isoformat() if detail.interview_date else None,
                "interview_time": detail.interview_time,
                "interview_round": detail.interview_round,
                "round_type": detail.round_type,
                "interview_type": detail.interview_type,
                "meeting_link": detail.meeting_link,
                "interviewer": detail.interviewer,
                "hr_notes": detail.hr_notes,
                "created_at": detail.created_at.isoformat(),
                "updated_at": detail.updated_at.isoformat(),
            })

        return jsonify({
            "interviews": result,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/applications/<id>/interview
# Get interview details for a specific application (HR view)
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/interview", methods=["GET"])
@hr_required
def hr_get_application_interview(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        interview_details = InterviewDetail.query.filter_by(
            application_id=application_id
        ).order_by(InterviewDetail.created_at).all()

        return jsonify({
            "application_id": application.id,
            "company": application.company,
            "role": application.role,
            "candidate_id": application.user_id,
            "interview_details": [i.to_dict(include_hr_notes=True) for i in interview_details],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# DELETE /api/hr/applications/<id>/interview
# Cancel/delete an interview
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/interview", methods=["DELETE"])
@hr_required
def hr_delete_interview(application_id):
    try:
        hr_user_id = int(get_jwt_identity())

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        # Delete all interview details for this application
        InterviewDetail.query.filter_by(application_id=application_id).delete()
        db.session.commit()

        # Notify candidate
        application = db.session.get(JobApplication, application_id)
        candidate = db.session.get(User, application.user_id)
        if candidate:
            publish_notification(
                user_id=application.user_id,
                notification_type="INTERVIEW_CANCELLED",
                message=f"Interview for {application.role} at {application.company} has been cancelled.",
                data={
                    "application_id": application.id,
                    "company": application.company,
                    "role": application.role,
                    "interview_id": application_id,
                },
            )

        db.session.add(AuditLog(
            user_id=hr_user_id,
            action="interview_cancelled",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
            },
        ))
        db.session.commit()

        return jsonify({
            "message": "Interview cancelled successfully",
            "application_id": application.id,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@hr_bp.route("/applications/bulk", methods=["POST"])
@hr_required
def hr_bulk_action():
    try:
        hr_user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        action = data.get("action")
        application_ids = data.get("application_ids", [])

        if not action or not application_ids:
            return jsonify({"error": "action and application_ids are required"}), 400

        if not isinstance(application_ids, list):
            return jsonify({"error": "application_ids must be a list"}), 400

        applications = JobApplication.query.filter(JobApplication.id.in_(application_ids)).all()
        app_map = {app.id: app for app in applications}

        results = {"success": [], "failed": [], "skipped": []}

        if action == "bulk_status_update":
            new_status_value = data.get("status")
            if not new_status_value:
                return jsonify({"error": "status is required for bulk_status_update"}), 400

            try:
                new_status = ApplicationStatus[new_status_value.upper()]
            except KeyError:
                return jsonify({"error": "Invalid status"}), 400

            notes = data.get("notes", f"Bulk status update to {new_status.value}")

            for app_id in application_ids:
                app = app_map.get(app_id)
                if not app:
                    results["failed"].append({"id": app_id, "reason": "Not found"})
                    continue

                blocked = require_candidate_active(app)
                if blocked is not None:
                    results["skipped"].append({"id": app_id, "reason": "Candidate disabled"})
                    continue

                blocked = require_application_workable(app)
                if blocked is not None:
                    results["skipped"].append({"id": app_id, "reason": "Application withdrawn"})
                    continue

                old_status = app.status
                if new_status == old_status:
                    results["skipped"].append({"id": app_id, "reason": "Status unchanged"})
                    continue

                allowed = STATUS_TRANSITIONS.get(old_status, [])
                if new_status not in allowed:
                    results["failed"].append({
                        "id": app_id,
                        "reason": f"Invalid transition {old_status.value} -> {new_status.value}"
                    })
                    continue

                app.status = new_status
                record_status_history(app, old_status, new_status, hr_user_id, notes)
                publish_notification(
                    user_id=app.user_id,
                    notification_type="APPLICATION_STATUS_CHANGED",
                    message=f"Your application for {app.role} at {app.company} has moved to {new_status.value}.",
                    data={"application_id": app.id, "company": app.company, "role": app.role,
                          "old_status": old_status.value, "new_status": new_status.value}
                )
                results["success"].append(app_id)

            db.session.add(AuditLog(
                admin_id=hr_user_id,
                action="bulk_status_update",
                details={"status": new_status.value, "count": len(application_ids)},
            ))
            db.session.commit()
            results["action"] = "bulk_status_update"
            results["new_status"] = new_status.value

        elif action == "shortlist":
            value = data.get("is_shortlisted", True)
            for app_id in application_ids:
                app = app_map.get(app_id)
                if not app:
                    results["failed"].append({"id": app_id, "reason": "Not found"})
                    continue
                old_value = app.is_shortlisted
                app.is_shortlisted = value
                if value:
                    publish_notification(
                        user_id=app.user_id,
                        notification_type="APPLICATION_SHORTLISTED",
                        message=f"Your application for {app.role} at {app.company} has been shortlisted!",
                        data={"application_id": app.id, "company": app.company, "role": app.role}
                    )
                db.session.add(AuditLog(
                    admin_id=hr_user_id,
                    action="application_shortlist_toggled",
                    target_user_id=app.user_id,
                    details={"application_id": app.id, "old_value": old_value, "new_value": value}
                ))
                results["success"].append(app_id)
            db.session.commit()
            results["action"] = "shortlist"
            results["is_shortlisted"] = value

        elif action == "delete":
            for app_id in application_ids:
                app = app_map.get(app_id)
                if not app:
                    results["failed"].append({"id": app_id, "reason": "Not found"})
                    continue
                cid = app.user_id
                company_name = app.company
                role_name = app.role
                try:
                    db.session.delete(app)
                    db.session.add(AuditLog(
                        admin_id=hr_user_id,
                        action="bulk_application_deleted",
                        target_user_id=cid,
                        details={"application_id": app_id, "company": company_name, "role": role_name}
                    ))
                except Exception:
                    results["failed"].append({"id": app_id, "reason": "Could not delete"})
                    continue
                results["success"].append(app_id)
            db.session.commit()
            results["action"] = "delete"

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

        return jsonify({"message": f"Bulk {action} completed", "results": results}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/analytics
# HR analytics aggregate endpoint
# ==============================================================

@hr_bp.route("/analytics", methods=["GET"])
@hr_required
def hr_analytics():
    try:
        from datetime import date, timedelta
        from sqlalchemy import func

        thirty_days_ago = date.today() - timedelta(days=30)

        status_counts = {}
        for status_val in ApplicationStatus:
            status_counts[status_val.value] = JobApplication.query.filter_by(
                status=status_val
            ).count()

        monthly_trend = (
            db.session.query(
                func.cast(JobApplication.applied_date, db.String(10)).label("day"),
                func.count().label("count")
            )
            .filter(JobApplication.applied_date >= thirty_days_ago)
            .group_by("day")
            .order_by("day")
            .all()
        )

        feedback_count = InterviewFeedback.query.count()
        rating_sum = db.session.query(
            func.avg(InterviewFeedback.rating)
        ).filter(InterviewFeedback.rating.isnot(None)).scalar()

        shortlisted_count = JobApplication.query.filter_by(is_shortlisted=True).count()

        # Feedback recommendation breakdown
        feedback_recs = db.session.query(
            InterviewFeedback.recommendation,
            func.count().label("count")
        ).filter(InterviewFeedback.recommendation.isnot(None)).group_by(
            InterviewFeedback.recommendation
        ).all()
        recommendation_counts = {"Hire": 0, "Maybe": 0, "No Hire": 0}
        for rec, count in feedback_recs:
            recommendation_counts[rec] = count

        top_companies = (
            db.session.query(JobApplication.company, func.count().label("count"))
            .group_by(JobApplication.company)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )

        active_candidates = User.query.filter_by(role=Role.USER, is_active=True).count()

        top_candidates = (
            db.session.query(
                User.name,
                User.email,
                func.count(JobApplication.id).label("app_count")
            )
            .join(JobApplication, User.id == JobApplication.user_id)
            .group_by(User.id)
            .order_by(func.count(JobApplication.id).desc())
            .limit(5)
            .all()
        )

        return jsonify({
            "status_counts": status_counts,
            "monthly_trend": [{"date": r[0], "count": r[1]} for r in monthly_trend],
            "feedback_count": feedback_count,
            "average_rating": round(float(rating_sum), 2) if rating_sum else None,
            "shortlisted_count": shortlisted_count,
            "top_companies": [{"company": r[0], "count": r[1]} for r in top_companies],
            "active_candidates": active_candidates,
            "top_candidates": [
                {"name": r[0], "email": r[1], "count": r[2]} for r in top_candidates
            ],
            "recommendation_counts": recommendation_counts,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/hr/applications/<id>/calendar
# HR gets calendar export data for interviews (iCal-compatible JSON)
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/calendar", methods=["GET"])
@hr_required
def hr_calendar_export(application_id):
    try:
        from datetime import datetime
        from dateutil import tz as dateutil_tz

        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        interviews = InterviewDetail.query.filter_by(
            application_id=application_id
        ).order_by(InterviewDetail.created_at).all()

        if not interviews:
            return jsonify({"error": "No interviews scheduled"}), 404

        events = []
        for interview in interviews:
            if not interview.interview_date or not interview.interview_time:
                continue
            date_obj = interview.interview_date
            time_str = interview.interview_time or "09:00"
            try:
                hour, minute = [int(x) for x in time_str.split(":")]
            except Exception:
                hour, minute = 9, 0

            user_tz = application.user.timezone or "UTC"
            try:
                local_tz = dateutil_tz.gettz(user_tz)
                dt_local = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, tzinfo=local_tz)
            except Exception:
                dt_local = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)

            events.append({
                "summary": f"{interview.interview_round or 'Interview'} - {application.role} at {application.company}",
                "description": (
                    f"Interview round: {interview.interview_round or 'N/A'}\n"
                    f"Type: {interview.interview_type or 'N/A'}\n"
                    f"Interviewer: {interview.interviewer or 'TBD'}\n"
                    f"Meeting: {interview.meeting_link or 'TBD'}"
                ),
                "dtstart": dt_local.isoformat() if dt_local else None,
                "dtend": dt_local.replace(hour=hour + 1) if dt_local else None,
                "url": interview.meeting_link,
            })

        return jsonify({
            "application": {"company": application.company, "role": application.role},
            "events": events,
            "format": "ical-compatible JSON",
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# Follow-up Reminder endpoints
# GET    /api/hr/reminders                        — list all HR-visible reminders
# GET    /api/hr/applications/<id>/reminders      — list reminders for an application
# POST   /api/hr/reminders                        — create reminder
# PATCH  /api/hr/reminders/<id>                   — update reminder
# DELETE /api/hr/reminders/<id>                   — delete reminder
# ==============================================================

@hr_bp.route("/reminders", methods=["GET"])
@hr_required
def list_reminders():
    try:
        status_filter = (request.args.get("status") or "").strip().upper()

        query = FollowUpReminder.query
        if status_filter:
            try:
                query = query.filter(FollowUpReminder.status == ReminderStatus[status_filter])
            except KeyError:
                return jsonify({"error": "Invalid status filter"}), 400

        query = query.order_by(FollowUpReminder.scheduled_at.desc())
        reminders = query.limit(500).all()

        result = []
        for r in reminders:
            app = db.session.get(JobApplication, r.application_id)
            item = r.to_dict()
            if app:
                item["application"] = {
                    "company": app.company,
                    "role": app.role,
                    "status": app.status.value,
                }
            result.append(item)

        return jsonify({"reminders": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/applications/<int:application_id>/reminders", methods=["GET"])
@hr_required
def list_application_reminders(application_id):
    try:
        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404
        reminders = FollowUpReminder.query.filter_by(application_id=application_id).order_by(FollowUpReminder.scheduled_at).all()
        return jsonify({"reminders": [r.to_dict() for r in reminders]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/reminders", methods=["POST"])
@hr_required
def create_reminder():
    try:
        hr_user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        schema = ReminderSchema()
        try:
            validated = schema.load(data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        application = db.session.get(JobApplication, validated["application_id"])
        if not application:
            return jsonify({"error": "Application not found"}), 404

        reminder_type_str = validated.get("reminder_type", "FOLLOW_UP")
        try:
            rtype = ReminderType[reminder_type_str]
        except KeyError:
            rtype = ReminderType.FOLLOW_UP

        reminder = FollowUpReminder(
            application_id=validated["application_id"],
            user_id=application.user_id,
            created_by_hr_id=hr_user_id,
            reminder_type=rtype,
            message=validated.get("message"),
            scheduled_at=validated["scheduled_at"],
            lead_time_minutes=validated.get("lead_time_minutes", 0),
        )
        db.session.add(reminder)
        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="reminder_created",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "reminder_type": reminder.reminder_type.value
            }
        ))
        db.session.commit()

        if application.user.email:
            publish_notification(
                user_id=application.user_id,
                notification_type="REMINDER_SCHEDULED",
                message=f"A follow-up reminder has been set: {reminder.message or 'Follow up on your application'}",
                data={
                    "reminder_id": reminder.id,
                    "application_id": application.id
                }
            )

        return jsonify({"message": "Reminder created", "reminder": reminder.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/reminders/<int:reminder_id>", methods=["PATCH"])
@hr_required
def update_reminder(reminder_id):
    try:
        reminder = db.session.get(FollowUpReminder, reminder_id)
        if not reminder:
            return jsonify({"error": "Reminder not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "message" in data:
            reminder.message = data["message"]
        if "scheduled_at" in data:
            reminder.scheduled_at = data["scheduled_at"]
        if "status" in data:
            try:
                reminder.status = ReminderStatus[data["status"].upper()]
            except KeyError:
                return jsonify({"error": "Invalid status"}), 400
        if "dismissed" in data:
            reminder.dismissed = bool(data["dismissed"])
            if reminder.dismissed:
                reminder.status = ReminderStatus.DISMISSED

        db.session.commit()
        return jsonify({"message": "Reminder updated", "reminder": reminder.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/reminders/<int:reminder_id>", methods=["DELETE"])
@hr_required
def delete_reminder(reminder_id):
    try:
        reminder = db.session.get(FollowUpReminder, reminder_id)
        if not reminder:
            return jsonify({"error": "Reminder not found"}), 404

        db.session.delete(reminder)
        db.session.commit()
        return jsonify({"message": "Reminder deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================
# PATCH /api/hr/applications/<id>/shortlist
# Toggle shortlist status on an application
# ==============================================================

@hr_bp.route("/applications/<int:application_id>/shortlist", methods=["PATCH"])
@hr_required
def toggle_shortlist(application_id):
    try:
        hr_user_id = int(get_jwt_identity())
        application = JobApplication.query.get(application_id)
        if not application:
            return jsonify({"error": "Application not found"}), 404

        blocked = require_application_workable(application)
        if blocked is not None:
            return blocked

        blocked = require_candidate_active(application)
        if blocked is not None:
            return blocked

        data = request.get_json() or {}
        new_value = data.get("is_shortlisted", not application.is_shortlisted)

        old_value = application.is_shortlisted
        application.is_shortlisted = bool(new_value)

        db.session.add(AuditLog(
            admin_id=hr_user_id,
            action="application_shortlist_toggled",
            target_user_id=application.user_id,
            details={
                "application_id": application.id,
                "old_value": old_value,
                "new_value": application.is_shortlisted,
            }
        ))
        db.session.commit()

        if application.is_shortlisted and application.user.email:
            publish_notification(
                user_id=application.user_id,
                notification_type="APPLICATION_SHORTLISTED",
                message=f"Your application for {application.role} at {application.company} has been shortlisted!",
                data={"application_id": application.id, "company": application.company, "role": application.role}
            )

        return jsonify({
            "message": "Shortlist status updated",
            "is_shortlisted": application.is_shortlisted,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
