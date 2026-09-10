from flask_jwt_extended import create_access_token, decode_token

from extensions import db
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
