import pytest

from app import app
from extensions import db
from models.user import User
from models.job import JobApplication, ApplicationStatus
from flask_jwt_extended import create_access_token


# ==========================================
# Test App
# ==========================================
@pytest.fixture(scope="function")
def test_app():

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


# ==========================================
# Test Client
# ==========================================
@pytest.fixture
def client(test_app):

    return test_app.test_client()


# ==========================================
# Test User
# ==========================================
@pytest.fixture
def test_user(test_app):

    user = User(
        name="API Test User",
        email="apitest@example.com",
        password="testpassword123"
    )

    db.session.add(user)
    db.session.commit()

    return user


# ==========================================
# JWT Authorization Headers
# ==========================================
@pytest.fixture
def auth_headers(test_app, test_user):

    with test_app.app_context():

        access_token = create_access_token(
            identity=str(test_user.id)
        )

    return {
        "Authorization": f"Bearer {access_token}"
    }


# ==========================================
# Create Application API
# ==========================================
def test_create_application_api(client, auth_headers):

    data = {
        "company": "Google",
        "role": "Software Engineer",
        "status": "APPLIED",
        "notes": "Applied through API test"
    }

    response = client.post(
        "/applications",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 201

    response_data = response.get_json()

    assert response_data["message"] == (
        "Application created successfully!"
    )

    assert response_data["application"]["company"] == "Google"
    assert response_data["application"]["role"] == "Software Engineer"
    assert response_data["application"]["status"] == "APPLIED"


# ==========================================
# Create Application - Missing Company
# ==========================================
def test_create_application_missing_company(client, auth_headers):

    data = {
        "role": "Software Engineer"
    }

    response = client.post(
        "/applications",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    assert response.get_json()["error"] == "Company is required"


# ==========================================
# Get All Applications API
# ==========================================
def test_get_all_applications_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Microsoft",
        role="Backend Developer",
        status=ApplicationStatus.APPLIED,
        notes="API test",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.get(
        "/applications",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "applications" in data
    assert "pagination" in data

    assert len(data["applications"]) == 1

    assert data["applications"][0]["company"] == "Microsoft"


# ==========================================
# Get Application By ID API
# ==========================================
def test_get_application_by_id_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Amazon",
        role="Python Developer",
        status=ApplicationStatus.INTERVIEW,
        notes="Interview round",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.get(
        f"/applications/{application.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["company"] == "Amazon"
    assert data["role"] == "Python Developer"
    assert data["status"] == "INTERVIEW"


# ==========================================
# Get Application Not Found API
# ==========================================
def test_get_application_not_found_api(
    client,
    auth_headers
):

    response = client.get(
        "/applications/99999",
        headers=auth_headers
    )

    assert response.status_code == 404


# ==========================================
# Update Application API
# ==========================================
def test_update_application_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Meta",
        role="Frontend Developer",
        status=ApplicationStatus.APPLIED,
        notes="Initial notes",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    updated_data = {
        "status": "INTERVIEW",
        "notes": "Interview scheduled"
    }

    response = client.put(
        f"/applications/{application.id}",
        json=updated_data,
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Application updated successfully!"
    )

    assert data["application"]["status"] == "INTERVIEW"
    assert data["application"]["notes"] == "Interview scheduled"


# ==========================================
# Delete Application API
# ==========================================
def test_delete_application_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Netflix",
        role="Software Developer",
        status=ApplicationStatus.APPLIED,
        notes="Delete API test",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.delete(
        f"/applications/{application.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Application deleted successfully!"
    )

    deleted_application = db.session.get(
        JobApplication,
        application.id
    )

    assert deleted_application is None


# ==========================================
# Unauthorized Request
# ==========================================
def test_unauthorized_request(client):

    response = client.get("/applications")

    assert response.status_code == 401