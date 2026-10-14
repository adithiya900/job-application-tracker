from flask_jwt_extended import create_access_token, decode_token

from extensions import bcrypt, db
from models.audit_log import AuditLog
from models.job import (
    ApplicationStatus,
    ApplicationStatusHistory,
    InterviewDetail,
    JobApplication,
)
from models.user import Role, User


def _headers_for(user):
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_impersonate_a_user_and_use_the_token(client, test_app):
    admin = User(
        name="Admin User",
        email="admin@gmail.com",
        password="admin123",
        role=Role.ADMIN,
    )
    user = User(
        name="Regular User",
        email="user@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    db.session.add_all((admin, user))
    db.session.commit()

    response = client.post(
        f"/api/admin/users/{user.id}/impersonate",
        headers=_headers_for(admin),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["impersonated_user"]["id"] == user.id

    decoded = decode_token(payload["access_token"])
    assert decoded["sub"] == str(user.id)
    assert decoded["impersonated_by"] == admin.id
    audit_log = AuditLog.query.one()
    assert audit_log.admin_id == admin.id
    assert audit_log.action == "user_impersonated"
    assert audit_log.target_user_id == user.id

    protected = client.get(
        "/api/applications",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert protected.status_code == 200


def test_impersonation_rejects_non_admin_self_and_missing_users(client, test_app):
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password="hashed-password",
        role=Role.ADMIN,
    )
    user = User(
        name="Regular User",
        email="user@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    db.session.add_all((admin, user))
    db.session.commit()

    assert client.post(
        f"/api/admin/users/{admin.id}/impersonate",
        headers=_headers_for(admin),
    ).status_code == 400
    assert client.post(
        "/api/admin/users/99999/impersonate",
        headers=_headers_for(admin),
    ).status_code == 404
    assert client.post(
        f"/api/admin/users/{admin.id}/impersonate",
        headers=_headers_for(user),
    ).status_code == 403


def test_admin_can_delete_user_and_their_applications(client, test_app):
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password="hashed-password",
        role=Role.ADMIN,
    )
    target = User(
        name="Target User",
        email="target@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    other_user = User(
        name="Other User",
        email="other@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    db.session.add_all((admin, target, other_user))
    db.session.flush()
    target_application = JobApplication(
        company="Target Company",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=target.id,
    )
    other_application = JobApplication(
        company="Other Company",
        role="Designer",
        status=ApplicationStatus.APPLIED,
        user_id=other_user.id,
    )
    db.session.add_all((target_application, other_application))
    db.session.commit()

    response = client.delete(
        f"/api/admin/users/{target.id}",
        headers=_headers_for(admin),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "User deleted successfully"
    assert db.session.get(User, target.id) is None
    assert db.session.get(JobApplication, target_application.id) is None
    assert db.session.get(JobApplication, other_application.id) is not None

    audit_log = AuditLog.query.one()
    assert audit_log.admin_id == admin.id
    assert audit_log.action == "user_deleted"
    assert audit_log.target_user_id == target.id
    assert audit_log.details["target_email"] == target.email


def test_delete_user_rejects_non_admin(client, test_app):
    user = User(
        name="Regular User",
        email="user@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    target = User(
        name="Target User",
        email="target@example.com",
        password="hashed-password",
        role=Role.USER,
    )
    db.session.add_all((user, target))
    db.session.commit()

    response = client.delete(
        f"/api/admin/users/{target.id}",
        headers=_headers_for(user),
    )

    assert response.status_code == 403
    assert db.session.get(User, target.id) is not None
    assert AuditLog.query.count() == 0


def test_delete_user_rejects_self_and_missing_users(client, test_app):
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password="hashed-password",
        role=Role.ADMIN,
    )
    db.session.add(admin)
    db.session.commit()

    self_response = client.delete(
        f"/api/admin/users/{admin.id}",
        headers=_headers_for(admin),
    )
    missing_response = client.delete(
        "/api/admin/users/99999",
        headers=_headers_for(admin),
    )

    assert self_response.status_code == 400
    assert missing_response.status_code == 404
    assert db.session.get(User, admin.id) is not None
    assert AuditLog.query.count() == 0


def _new_user(email, role):
    user = User(
        name=email.split("@")[0],
        email=email,
        password=bcrypt.generate_password_hash("admin-test-password").decode("utf-8"),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_admin_dashboard_and_management_routes_are_role_protected(client, test_app):
    admin = _new_user("admin-dashboard@example.com", Role.ADMIN)
    candidate = _new_user("candidate-dashboard@example.com", Role.USER)
    hr = _new_user("hr-dashboard@example.com", Role.HR)

    assert client.get("/api/admin/dashboard").status_code == 401
    for restricted_user in (candidate, hr):
        headers = _headers_for(restricted_user)
        for path in (
            "/api/admin/dashboard",
            "/api/admin/users",
            "/api/admin/applications",
            "/api/admin/activity",
        ):
            assert client.get(path, headers=headers).status_code == 403
        assert client.post(
            "/api/admin/users",
            headers=headers,
            json={
                "name": "Blocked User",
                "email": "blocked@example.com",
                "password": "initial-password",
                "role": "USER",
            },
        ).status_code == 403
        assert client.patch(
            "/api/admin/applications/1/status",
            headers=headers,
            json={"status": "UNDER_REVIEW"},
        ).status_code == 403
        assert client.patch(
            "/api/admin/applications/1",
            headers=headers,
            json={"company": "Blocked Company"},
        ).status_code == 403

    for path in (
        "/api/admin/dashboard",
        "/api/admin/users",
        "/api/admin/applications",
        "/api/admin/activity",
    ):
        assert client.get(path, headers=_headers_for(admin)).status_code == 200


def test_admin_user_create_update_and_last_admin_protection(client, test_app):
    admin = _new_user("admin-users@example.com", Role.ADMIN)
    headers = _headers_for(admin)

    created = client.post(
        "/api/admin/users",
        headers=headers,
        json={
            "name": "New HR",
            "email": "new-hr@example.com",
            "password": "initial-password",
            "role": "HR",
        },
    )
    assert created.status_code == 201
    created_user_id = created.get_json()["user"]["id"]
    created_user = db.session.get(User, created_user_id)
    assert created_user.role == Role.HR
    assert bcrypt.check_password_hash(created_user.password, "initial-password")

    updated = client.patch(
        f"/api/admin/users/{created_user_id}",
        headers=headers,
        json={"role": "USER"},
    )
    assert updated.status_code == 200
    assert db.session.get(User, created_user_id).role == Role.USER
    assert AuditLog.query.count() == 2

    assert client.patch(
        f"/api/admin/users/{admin.id}",
        headers=headers,
        json={"role": "USER"},
    ).status_code == 409


def test_admin_can_manage_applications_and_status_history(client, test_app, monkeypatch):
    admin = _new_user("admin-apps@example.com", Role.ADMIN)
    candidate = _new_user("candidate-apps@example.com", Role.USER)
    application = JobApplication(
        company="Example Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()

    import api.hr

    monkeypatch.setattr(api.hr, "send_status_notification", lambda *args: None)
    response = client.patch(
        f"/api/admin/applications/{application.id}/status",
        headers=_headers_for(admin),
        json={"status": "WITHDRAWN", "notes": "Admin correction"},
    )
    assert response.status_code == 200
    assert db.session.get(JobApplication, application.id).status == ApplicationStatus.WITHDRAWN
    history = ApplicationStatusHistory.query.filter_by(
        application_id=application.id
    ).one()
    assert history.new_status == ApplicationStatus.WITHDRAWN
    assert history.changed_by == admin.id

    invalid = client.patch(
        f"/api/admin/applications/{application.id}/status",
        headers=_headers_for(admin),
        json={"status": "OFFER"},
    )
    assert invalid.status_code == 422

    detail = client.get(
        f"/api/admin/applications/{application.id}",
        headers=_headers_for(admin),
    )
    assert detail.status_code == 200
    assert detail.get_json()["status_history"][0]["notes"] == "Admin correction"


def test_admin_can_edit_and_reassign_application_safely(client, test_app, monkeypatch):
    admin = _new_user("admin-edit-app@example.com", Role.ADMIN)
    old_candidate = _new_user("old-candidate@example.com", Role.USER)
    new_candidate = _new_user("new-candidate@example.com", Role.USER)
    inactive_candidate = _new_user("inactive-candidate@example.com", Role.USER)
    inactive_candidate.is_active = False
    hr_user = _new_user("hr-edit-app@example.com", Role.HR)
    application = JobApplication(
        company="Original Co",
        role="Engineer",
        status=ApplicationStatus.UNDER_REVIEW,
        notes="Original notes",
        user_id=old_candidate.id,
    )
    duplicate = JobApplication(
        company="Target Co",
        role="Analyst",
        status=ApplicationStatus.APPLIED,
        user_id=new_candidate.id,
    )
    same_candidate_duplicate = JobApplication(
        company="Existing Co",
        role="Designer",
        status=ApplicationStatus.APPLIED,
        user_id=old_candidate.id,
    )
    db.session.add_all((application, duplicate, same_candidate_duplicate))
    db.session.commit()
    applied_date = application.applied_date

    import services.notification_service as notification_service
    import api.admin as admin_api

    notifications = []
    capture_notification = lambda user_id, notification_type, message, data=None: notifications.append(
        (user_id, notification_type, data)
    )
    monkeypatch.setattr(
        notification_service,
        "publish_notification",
        capture_notification,
    )
    monkeypatch.setattr(admin_api, "publish_notification", capture_notification)
    headers = _headers_for(admin)

    inactive_response = client.patch(
        f"/api/admin/applications/{application.id}",
        headers=headers,
        json={"company": "Must Not Persist", "candidate_email": inactive_candidate.email},
    )
    assert inactive_response.status_code == 404
    assert application.company == "Original Co"
    assert application.user_id == old_candidate.id

    role_response = client.patch(
        f"/api/admin/applications/{application.id}",
        headers=headers,
        json={"candidate_email": hr_user.email},
    )
    assert role_response.status_code == 404

    same_candidate_duplicate_response = client.patch(
        f"/api/admin/applications/{application.id}",
        headers=headers,
        json={
            "company": "Existing Co",
            "role": "Designer",
        },
    )
    assert same_candidate_duplicate_response.status_code == 409
    assert application.company == "Original Co"

    duplicate_response = client.patch(
        f"/api/admin/applications/{application.id}",
        headers=headers,
        json={
            "company": "Target Co",
            "role": "Analyst",
            "candidate_email": new_candidate.email,
        },
    )
    assert duplicate_response.status_code == 409
    assert application.company == "Original Co"
    assert application.user_id == old_candidate.id

    response = client.patch(
        f"/api/admin/applications/{application.id}",
        headers=headers,
        json={
            "company": "New Co",
            "role": "Manager",
            "notes": "Reviewed by admin",
            "candidate_email": f" {new_candidate.email.upper()} ",
        },
    )

    assert response.status_code == 200
    db.session.refresh(application)
    assert application.company == "New Co"
    assert application.role == "Manager"
    assert application.notes == "Reviewed by admin"
    assert application.user_id == new_candidate.id
    assert application.status == ApplicationStatus.UNDER_REVIEW
    assert application.applied_date == applied_date
    assert ApplicationStatusHistory.query.filter_by(application_id=application.id).count() == 0

    audit = AuditLog.query.filter_by(action="application_updated").one()
    assert audit.admin_id == admin.id
    assert audit.target_user_id == new_candidate.id
    assert audit.details["changes"]["candidate"] == {
        "from": old_candidate.email,
        "to": new_candidate.email,
    }
    candidate_notifications = [
        notification for notification in notifications
        if notification[1] == "APPLICATION_UPDATED"
    ]
    assert {notification[0] for notification in candidate_notifications} == {
        old_candidate.id,
        new_candidate.id,
    }
    assert all(notification[2]["reassigned"] for notification in candidate_notifications)


def test_admin_can_delete_an_application_and_cannot_delete_last_admin(client, test_app):
    admin = _new_user("admin-delete@example.com", Role.ADMIN)
    candidate = _new_user("candidate-delete@example.com", Role.USER)
    application = JobApplication(
        company="Remove Co",
        role="Analyst",
        user_id=candidate.id,
        status=ApplicationStatus.APPLIED,
    )
    db.session.add(application)
    db.session.commit()

    assert client.delete(
        f"/api/admin/users/{admin.id}",
        headers=_headers_for(admin),
    ).status_code == 400
    assert client.delete(
        f"/api/admin/applications/{application.id}",
        headers=_headers_for(admin),
    ).status_code == 200
    assert db.session.get(JobApplication, application.id) is None


def test_disabling_user_revokes_existing_tokens_and_blocks_login(client, test_app):
    admin = _new_user("admin-disable@example.com", Role.ADMIN)
    target = _new_user("target-disable@example.com", Role.USER)
    target_headers = _headers_for(target)

    response = client.patch(
        f"/api/admin/users/{target.id}",
        headers=_headers_for(admin),
        json={"is_active": False},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["is_active"] is False

    protected_response = client.get(
        "/api/applications",
        headers=target_headers,
    )
    assert protected_response.status_code == 401

    login_response = client.post(
        "/login",
        json={"email": target.email, "password": "admin-test-password"},
    )
    assert login_response.status_code == 403


def test_admin_application_view_filters_return_200(client, test_app):
    """Regression: the interviews view must not use .has() on a collection."""
    admin = _new_user("admin-views@example.com", Role.ADMIN)
    candidate = _new_user("candidate-views@example.com", Role.USER)
    headers = _headers_for(admin)

    with_interview = JobApplication(
        user_id=candidate.id,
        company="Viewed Corp",
        role="Engineer",
        status=ApplicationStatus.INTERVIEW,
    )
    without_interview = JobApplication(
        user_id=candidate.id,
        company="Plain Corp",
        role="Designer",
        status=ApplicationStatus.APPLIED,
    )
    db.session.add_all((with_interview, without_interview))
    db.session.commit()

    db.session.add(InterviewDetail(
        application_id=with_interview.id,
        interview_round="Technical Round 1",
        round_type="Technical",
    ))
    db.session.commit()

    for view in ("", "all", "interviews", "feedback"):
        response = client.get(
            "/api/admin/applications",
            query_string={"view": view},
            headers=headers,
        )
        assert response.status_code == 200, view
        assert "applications" in response.get_json()

    interviews = client.get(
        "/api/admin/applications",
        query_string={"view": "interviews"},
        headers=headers,
    ).get_json()["applications"]
    assert any(app["id"] == with_interview.id for app in interviews)
    assert all(app["id"] != without_interview.id for app in interviews)

    assert client.get(
        "/api/admin/applications",
        query_string={"view": "bogus"},
        headers=headers,
    ).status_code == 400
