from extensions import db
from models.user import Role, User
from models.job import JobApplication
from models.audit_log import AuditLog


def _headers_for(user):
    from flask_jwt_extended import create_access_token

    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_users(integration_client):
    admin = User(
        name="Integration Admin",
        email="integration-admin@example.com",
        password="hashed-password",
        role=Role.ADMIN,
    )

    user = User(
        name="Integration User",
        email="integration-user@example.com",
        password="hashed-password",
        role=Role.USER,
    )

    db.session.add_all([admin, user])
    db.session.commit()

    response = integration_client.get(
        "/api/admin/users",
        headers=_headers_for(admin),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert len(data["users"]) == 2

    admin_data = next(
        item for item in data["users"]
        if item["id"] == admin.id
    )

    user_data = next(
        item for item in data["users"]
        if item["id"] == user.id
    )

    assert admin_data["role"] == "ADMIN"
    assert admin_data["is_current_user"] is True

    assert user_data["role"] == "USER"
    assert user_data["is_current_user"] is False
    

def test_admin_delete_user_cascade_and_audit(integration_client):
    admin = User(
        name="Delete Admin",
        email="delete-admin@example.com",
        password="hashed-password",
        role=Role.ADMIN,
    )

    target_user = User(
        name="Delete Target",
        email="delete-target@example.com",
        password="hashed-password",
        role=Role.USER,
    )

    db.session.add_all([admin, target_user])
    db.session.commit()

    application = JobApplication(
        user_id=target_user.id,
        company="Cascade Company",
        role="Backend Developer",
        status="APPLIED",
    )

    db.session.add(application)
    db.session.commit()

    application_id = application.id
    target_user_id = target_user.id

    response = integration_client.delete(
        f"/api/admin/users/{target_user_id}",
        headers=_headers_for(admin),
    )

    assert response.status_code == 200

    assert db.session.get(User, target_user_id) is None
    assert db.session.get(JobApplication, application_id) is None

    audit_log = AuditLog.query.filter_by(
        action="user_deleted",
        target_user_id=target_user_id,
    ).first()

    assert audit_log is not None
    assert audit_log.admin_id == admin.id