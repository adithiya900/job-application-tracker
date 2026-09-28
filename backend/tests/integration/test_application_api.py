from flask_jwt_extended import create_access_token

from extensions import db
from models.job import JobApplication


def _auth_headers(user_id):
    token = create_access_token(identity=str(user_id))
    return {"Authorization": f"Bearer {token}"}


def test_application_crud_uses_postgres(integration_client):
    from models.user import User

    user = User(
        name="Integration User",
        email="crud-integration@example.com",
        password="hashed-password",
    )

    db.session.add(user)
    db.session.commit()

    headers = _auth_headers(user.id)

    # CREATE
    create_response = integration_client.post(
        "/applications",
        json={
            "company": "Integration Company",
            "role": "Backend Developer",
            "status": "APPLIED",
            "notes": "PostgreSQL integration test",
        },
        headers=headers,
    )
    print("CREATE RESPONSE:", create_response.status_code, create_response.get_json())

    assert create_response.status_code == 201

    created_data = create_response.get_json()
    application_id = created_data["application"]["id"]

    # READ
    get_response = integration_client.get(
        f"/applications/{application_id}",
        headers=headers,
    )

    assert get_response.status_code == 200

    application_data = get_response.get_json()

    assert application_data["company"] == "Integration Company"
    assert application_data["role"] == "Backend Developer"
    assert application_data["status"] == "APPLIED"

    # Verify actual database row
    application = db.session.get(
        JobApplication,
        application_id,
    )

    assert application is not None
    assert application.company == "Integration Company"
    assert application.user_id == user.id

    # UPDATE
    update_response = integration_client.put(
        f"/applications/{application_id}",
        json={
            "status": "INTERVIEW",
            "notes": "Interview scheduled",
        },
        headers=headers,
    )

    assert update_response.status_code == 200

    updated_data = update_response.get_json()

    assert updated_data["application"]["status"] == "INTERVIEW"

    # DELETE
    delete_response = integration_client.delete(
        f"/applications/{application_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    assert db.session.get(
        JobApplication,
        application_id,
    ) is None