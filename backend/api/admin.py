from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import func, or_
from extensions import bcrypt, cache, db
from models.audit_log import AuditLog
from models.job import (
    ApplicationStatus,
    ApplicationStatusHistory,
    InterviewDetail,
    InterviewFeedback,
    JobApplication,
    STATUS_TRANSITIONS,
)
from models.user import Role, User
from services.application_service import ApplicationService
from services.notification_service import (
    publish_admin_notification,
    publish_notification,
)
from utils.admin import admin_required


admin_bp = Blueprint("admin", __name__)


def _audit(admin_id, action, target_user_id=None, details=None):
    db.session.add(AuditLog(
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        details=details or {},
    ))


def _user_data(user, current_user_id):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "application_count": JobApplication.query.filter_by(user_id=user.id).count(),
        "is_current_user": user.id == current_user_id,
    }


def _application_data(application, include_details=False):
    candidate = db.session.get(User, application.user_id)
    result = {
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "applied_date": application.applied_date.isoformat() if application.applied_date else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
        "interview_at": application.interview_at.isoformat() if application.interview_at else None,
        "notes": application.notes,
        "resume_path": application.resume_path,
        "user_id": application.user_id,
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
        } if candidate else None,
        "interview_details": (
            application.interview_details.to_dict(include_hr_notes=True)
            if application.interview_details else None
        ),
    }
    if include_details:
        result["status_history"] = [
            item.to_dict() for item in application.status_history
        ]
        result["feedback"] = [
            item.to_dict(include_internal=True)
            for item in application.feedback
        ]
    return result


def _page_payload(pagination, items, key):
    return {
        key: items,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def dashboard():
    role_counts = {
        role.value: User.query.filter_by(role=role).count()
        for role in Role
    }
    status_counts = {
        status.value: JobApplication.query.filter_by(status=status).count()
        for status in ApplicationStatus
    }
    now = date.today()
    upcoming = (
        InterviewDetail.query
        .filter(InterviewDetail.interview_date >= now)
        .order_by(InterviewDetail.interview_date, InterviewDetail.interview_time)
        .limit(8)
        .all()
    )
    recent_applications = (
        JobApplication.query
        .order_by(JobApplication.updated_at.desc(), JobApplication.id.desc())
        .limit(8)
        .all()
    )
    recent_users = (
        User.query
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(8)
        .all()
    )
    recent_history = (
        ApplicationStatusHistory.query
        .order_by(ApplicationStatusHistory.changed_at.desc())
        .limit(8)
        .all()
    )

    return jsonify({
        "users": {
            "total": User.query.count(),
            "by_role": role_counts,
            "recent": [
                _user_data(user, int(get_jwt_identity()))
                for user in recent_users
            ],
        },
        "applications": {
            "total": JobApplication.query.count(),
            "by_status": status_counts,
            "recent": [_application_data(app) for app in recent_applications],
        },
        "interviews": {
            "total": InterviewDetail.query.count(),
            "upcoming": [
                {
                    "application_id": item.application_id,
                    "application": _application_data(item.application),
                    "details": item.to_dict(include_hr_notes=True),
                }
                for item in upcoming
            ],
        },
        "feedback_count": InterviewFeedback.query.count(),
        "recent_status_changes": [
            {
                **item.to_dict(),
                "application": {
                    "company": item.application.company,
                    "role": item.application.role,
                    "candidate": item.application.user.name,
                },
            }
            for item in recent_history
        ],
    }), 200


@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def list_users():
    current_user_id = int(get_jwt_identity())
    search = (request.args.get("search") or "").strip()
    role_value = (request.args.get("role") or "").strip().upper()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)

    query = User.query
    if search:
        term = f"%{search}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))
    if role_value:
        try:
            query = query.filter(User.role == Role[role_value])
        except KeyError:
            return jsonify({"error": "Invalid role filter"}), 400

    pagination = query.order_by(User.created_at.desc(), User.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    payload = _page_payload(
        pagination,
        [_user_data(user, current_user_id) for user in pagination.items],
        "users",
    )
    payload["count"] = pagination.total
    return jsonify(payload), 200


@admin_bp.route("/api/admin/users", methods=["POST"])
@admin_required
def create_user():
    admin_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    role_value = (data.get("role") or "").strip().upper()

    if not name or len(name) > 100:
        return jsonify({"error": "Name is required and must be 100 characters or fewer"}), 400
    if not email or len(email) > 120 or "@" not in email:
        return jsonify({"error": "A valid email address is required"}), 400
    if (
        not isinstance(password, str)
        or len(password) < 8
        or len(password.encode("utf-8")) > 72
    ):
        return jsonify({"error": "Password must be 8 to 72 UTF-8 bytes"}), 400
    try:
        role = Role[role_value]
    except KeyError:
        return jsonify({"error": "Invalid role"}), 400
    if User.query.filter(func.lower(User.email) == email).first():
        return jsonify({"error": "Email address is already in use"}), 409

    user = User(
        name=name,
        email=email,
        password=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    _audit(admin_id, "user_created", user.id, {"email": email, "role": role.value})
    db.session.commit()
    publish_admin_notification(
        "ADMIN_USER_CREATED",
        f"Admin created a {role.value} account for {email}.",
        {"user_id": user.id, "role": role.value},
    )
    return jsonify({
        "message": "User created successfully",
        "user": _user_data(user, admin_id),
    }), 201


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@admin_required
def update_user(user_id):
    admin_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    unsupported = set(data) - {"name", "email", "role", "is_active"}
    if unsupported:
        return jsonify({"error": "Unsupported user fields"}), 400
    if not data:
        return jsonify({"error": "No user fields provided"}), 400
    updates = {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name or len(name) > 100:
            return jsonify({"error": "Name is required and must be 100 characters or fewer"}), 400
        user.name = name
        updates["name"] = name
    if "email" in data:
        email = (data.get("email") or "").strip().lower()
        if not email or len(email) > 120 or "@" not in email:
            return jsonify({"error": "A valid email address is required"}), 400
        duplicate = User.query.filter(
            func.lower(User.email) == email,
            User.id != user.id,
        ).first()
        if duplicate:
            return jsonify({"error": "Email address is already in use"}), 409
        user.email = email
        updates["email"] = email
    if "role" in data:
        old_role = user.role
        try:
            new_role = Role[(data.get("role") or "").strip().upper()]
        except (KeyError, AttributeError):
            return jsonify({"error": "Invalid role"}), 400
        if new_role != user.role and user.role == Role.ADMIN:
            admin_count = User.query.filter_by(role=Role.ADMIN).count()
            if user.id == admin_id:
                return jsonify({"error": "You cannot change your own admin role"}), 409
            if admin_count <= 1:
                return jsonify({"error": "The last admin cannot be demoted"}), 409
        user.role = new_role
        if new_role != old_role:
            updates["old_role"] = old_role.value
        updates["role"] = new_role.value
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "Account status must be a boolean"}), 400
        if user.id == admin_id and not data["is_active"]:
            return jsonify({"error": "You cannot disable your own admin account"}), 409
        if user.role == Role.ADMIN and user.is_active and not data["is_active"]:
            active_admins = User.query.filter_by(role=Role.ADMIN, is_active=True).count()
            if active_admins <= 1:
                return jsonify({"error": "The last active admin cannot be disabled"}), 409
        user.is_active = data["is_active"]
        updates["is_active"] = data["is_active"]

    _audit(admin_id, "user_updated", user.id, updates)
    db.session.commit()
    publish_admin_notification(
        "ADMIN_USER_UPDATED",
        f"Admin updated {user.email}'s account.",
        {"user_id": user.id, "role": user.role.value, "is_active": user.is_active},
    )
    return jsonify({
        "message": "User updated successfully",
        "user": _user_data(user, admin_id),
    }), 200


@admin_bp.route("/api/admin/users/<int:user_id>/impersonate", methods=["POST"])
@admin_required
def impersonate_user(user_id):
    current_admin_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == current_admin_id:
        return jsonify({"error": "Admin cannot impersonate themselves"}), 400

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"impersonated_by": current_admin_id},
    )
    _audit(current_admin_id, "user_impersonated", user.id, {"target_email": user.email})
    db.session.commit()
    return jsonify({
        "message": "User impersonation token created",
        "impersonated_user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
        },
        "access_token": token,
    }), 200


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    current_admin_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == current_admin_id:
        return jsonify({"error": "Admin cannot delete themselves"}), 400
    if user.role == Role.ADMIN and User.query.filter_by(role=Role.ADMIN).count() <= 1:
        return jsonify({"error": "The last admin cannot be deleted"}), 409

    _audit(current_admin_id, "user_deleted", user.id, {
        "target_email": user.email,
        "target_role": user.role.value,
    })
    deleted_email = user.email
    db.session.delete(user)
    db.session.commit()
    publish_admin_notification(
        "ADMIN_USER_DELETED",
        f"Admin deleted the account {deleted_email}.",
        {"user_id": user_id},
    )
    return jsonify({"message": "User deleted successfully"}), 200


@admin_bp.route("/api/admin/applications", methods=["GET"])
@admin_required
def list_applications():
    search = (request.args.get("search") or "").strip()
    status_value = (request.args.get("status") or "").strip().upper()
    view = (request.args.get("view") or "").strip().lower()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)

    query = JobApplication.query
    if search:
        term = f"%{search}%"
        query = query.join(User, JobApplication.user_id == User.id).filter(
            or_(
                JobApplication.company.ilike(term),
                JobApplication.role.ilike(term),
                User.name.ilike(term),
                User.email.ilike(term),
            )
        )
    if status_value:
        try:
            query = query.filter(JobApplication.status == ApplicationStatus[status_value])
        except KeyError:
            return jsonify({"error": "Invalid status filter"}), 400
    if view == "interviews":
        query = query.filter(JobApplication.interview_details.has())
    elif view == "feedback":
        query = query.filter(JobApplication.feedback.any())
    elif view not in ("", "all"):
        return jsonify({"error": "Invalid application view"}), 400

    pagination = query.order_by(
        JobApplication.updated_at.desc(), JobApplication.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(_page_payload(
        pagination,
        [_application_data(app) for app in pagination.items],
        "applications",
    )), 200


@admin_bp.route("/api/admin/applications/<int:application_id>", methods=["GET"])
@admin_required
def get_application(application_id):
    application = db.session.get(JobApplication, application_id)
    if application is None:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(_application_data(application, include_details=True)), 200


@admin_bp.route(
    "/api/admin/applications/<int:application_id>",
    methods=["PATCH"],
)
@admin_required
def update_application(application_id):
    admin_id = int(get_jwt_identity())
    application = db.session.get(JobApplication, application_id)
    if application is None:
        return jsonify({"error": "Application not found"}), 404

    data = request.get_json(silent=True) or {}
    unsupported = set(data) - {"company", "role", "notes", "candidate_email"}
    if unsupported:
        return jsonify({"error": "Unsupported application fields"}), 400
    if not data:
        return jsonify({"error": "No application fields provided"}), 400

    updates = {}
    changes = {}
    for field, limit in (("company", 100), ("role", 100)):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
                return jsonify({
                    "error": f"{field.capitalize()} is required and must be {limit} characters or fewer"
                }), 400
            value = value.strip()
            if getattr(application, field) != value:
                updates[field] = {"from": getattr(application, field), "to": value}
                changes[field] = value

    if "notes" in data:
        notes = data["notes"]
        if notes is not None and (
            not isinstance(notes, str) or len(notes) > 5000
        ):
            return jsonify({"error": "Notes must be 5000 characters or fewer"}), 400
        notes = notes.strip() if notes else None
        if application.notes != notes:
            updates["notes"] = {
                "from": application.notes,
                "to": notes,
            }
            changes["notes"] = notes

    old_candidate = db.session.get(User, application.user_id)
    new_candidate = old_candidate
    application_reassigned = False
    if "candidate_email" in data:
        candidate_email = data["candidate_email"]
        if not isinstance(candidate_email, str) or not candidate_email.strip():
            return jsonify({"error": "A candidate email address is required"}), 400
        candidate_email = candidate_email.strip().lower()
        new_candidate = User.query.filter(
            func.lower(User.email) == candidate_email,
            User.role == Role.USER,
        ).first()
        if new_candidate is None or (
            new_candidate.id != application.user_id and not new_candidate.is_active
        ):
            return jsonify({"error": "Active candidate account not found"}), 404
        application_reassigned = new_candidate.id != application.user_id
        if application_reassigned:
            updates["candidate"] = {
                "from": old_candidate.email if old_candidate else None,
                "to": new_candidate.email,
            }
            changes["user_id"] = new_candidate.id

    company = changes.get("company", application.company)
    role = changes.get("role", application.role)
    job_details_changed = (
        company.lower() != application.company.lower()
        or role.lower() != application.role.lower()
    )
    if application_reassigned or job_details_changed:
        duplicate = JobApplication.query.filter(
            JobApplication.id != application.id,
            JobApplication.user_id == new_candidate.id,
            func.lower(JobApplication.company) == company.lower(),
            func.lower(JobApplication.role) == role.lower(),
        ).first()
        if duplicate:
            return jsonify({
                "error": "The candidate already has an application for this company and role"
            }), 409

    if not updates:
        return jsonify({
            "message": "Application unchanged",
            "application": _application_data(application, include_details=True),
        }), 200

    for field, value in changes.items():
        setattr(application, field, value)
    _audit(admin_id, "application_updated", application.user_id, {
        "application_id": application.id,
        "changes": updates,
    })
    db.session.commit()
    cache.delete(f"analytics:user:{application.user_id}")
    if old_candidate and old_candidate.id != application.user_id:
        cache.delete(f"analytics:user:{old_candidate.id}")

    recipients = {candidate.id: candidate for candidate in (old_candidate, new_candidate) if candidate}
    for candidate in recipients.values():
        publish_notification(
            candidate.id,
            "APPLICATION_UPDATED",
            f"An administrator updated the application for {application.role} at {application.company}.",
            {
                "application_id": application.id,
                "company": application.company,
                "role": application.role,
                "reassigned": application_reassigned,
            },
        )
    publish_admin_notification(
        "ADMIN_APPLICATION_UPDATED",
        f"Admin updated the {application.role} application at {application.company}.",
        {"application_id": application.id, "candidate_id": application.user_id},
    )
    return jsonify({
        "message": "Application updated successfully",
        "application": _application_data(application, include_details=True),
    }), 200


@admin_bp.route(
    "/api/admin/applications/<int:application_id>",
    methods=["DELETE"],
)
@admin_required
def delete_application(application_id):
    admin_id = int(get_jwt_identity())
    application = db.session.get(JobApplication, application_id)
    if application is None:
        return jsonify({"error": "Application not found"}), 404
    _audit(admin_id, "application_deleted", application.user_id, {
        "application_id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
    })
    company = application.company
    role = application.role
    candidate_id = application.user_id
    ApplicationService.delete_application(application.id, application.user_id)
    publish_admin_notification(
        "ADMIN_APPLICATION_DELETED",
        f"Admin deleted the {role} application at {company}.",
        {"application_id": application_id, "candidate_id": candidate_id},
    )
    return jsonify({"message": "Application deleted successfully"}), 200


@admin_bp.route(
    "/api/admin/applications/<int:application_id>/status",
    methods=["PATCH"],
)
@admin_required
def update_application_status(application_id):
    admin_id = int(get_jwt_identity())
    application = db.session.get(JobApplication, application_id)
    if application is None:
        return jsonify({"error": "Application not found"}), 404
    data = request.get_json(silent=True) or {}
    status_value = data.get("status")
    if not isinstance(status_value, str):
        return jsonify({"error": "Status is required"}), 400
    try:
        new_status = ApplicationStatus[status_value.upper()]
    except KeyError:
        return jsonify({"error": "Invalid status"}), 400

    old_status = application.status
    if new_status == old_status:
        return jsonify({
            "message": "Status unchanged",
            "application": _application_data(application),
        }), 200
    allowed = STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        return jsonify({
            "error": f"Invalid status transition from {old_status.value} to {new_status.value}",
            "allowed_transitions": [status.value for status in allowed],
        }), 422

    application.status = new_status
    db.session.add(ApplicationStatusHistory(
        application_id=application.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=admin_id,
        notes=data.get("notes"),
    ))
    _audit(admin_id, "application_status_updated", application.user_id, {
        "application_id": application.id,
        "company": application.company,
        "role": application.role,
        "old_status": old_status.value,
        "new_status": new_status.value,
    })
    db.session.commit()
    cache.delete(f"analytics:user:{application.user_id}")

    from api.hr import send_status_notification

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
        "application": _application_data(application),
    }), 200


@admin_bp.route("/api/admin/activity", methods=["GET"])
@admin_required
def list_activity():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    search = (request.args.get("search") or "").strip()
    query = AuditLog.query
    if search:
        term = f"%{search}%"
        query = query.filter(AuditLog.action.ilike(term))
    pagination = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    entries = []
    for item in pagination.items:
        actor = db.session.get(User, item.admin_id)
        target = db.session.get(User, item.target_user_id) if item.target_user_id else None
        entries.append({
            "id": item.id,
            "admin_id": item.admin_id,
            "admin_name": actor.name if actor else "Deleted admin",
            "action": item.action,
            "target_user_id": item.target_user_id,
            "target_user_name": target.name if target else None,
            "details": item.details or {},
            "created_at": item.created_at.isoformat(),
        })
    return jsonify(_page_payload(pagination, entries, "activity")), 200
