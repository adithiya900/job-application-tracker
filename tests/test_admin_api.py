from flask_jwt_extended import create_access_token, decode_token

from extensions import db
from models.audit_log import AuditLog
from models.job import ApplicationStatus, JobApplication
from models.user import Role, User


def _headers_for(user):
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_impersonate_a_user_and_use_the_token(client, test_app):
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
