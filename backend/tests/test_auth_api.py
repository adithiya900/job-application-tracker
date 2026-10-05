import pytest
from sqlalchemy import create_engine

from app import app
from extensions import db, bcrypt
from models.user import User, Role


# ==========================================
# Test App
# ==========================================

@pytest.fixture(scope="function")
def test_app():

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    original_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    original_engines = db._app_engines[app]
    test_engine = create_engine("sqlite:///:memory:")
    db._app_engines[app] = {None: test_engine}

    with app.app_context():

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()
        test_engine.dispose()
        db._app_engines[app] = original_engines
        app.config["SQLALCHEMY_DATABASE_URI"] = original_uri


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

    hashed_password = bcrypt.generate_password_hash(
        "testpassword123"
    ).decode("utf-8")

    user = User(
        name="Test User",
        email="testuser@example.com",
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return user


# ==========================================
# Test User with Token
# ==========================================

@pytest.fixture
def auth_headers(client, test_user):

    from flask_jwt_extended import create_access_token

    access_token = create_access_token(
        identity=str(test_user.id),
        additional_claims={"role": test_user.role.value}
    )

    return {"Authorization": f"Bearer {access_token}"}


# ==========================================
# Register User - Success
# ==========================================

def test_register_user_success(client):

    data = {
        "name": "Adithiya",
        "email": "adithiya@example.com",
        "password": "password123"
    }

    response = client.post(
        "/register",
        json=data
    )

    assert response.status_code == 201

    response_data = response.get_json()

    assert response_data["message"] == (
        "User registered successfully!"
    )

    assert response_data["user"]["name"] == "Adithiya"

    assert response_data["user"]["email"] == (
        "adithiya@example.com"
    )

    assert "id" in response_data["user"]


# ==========================================
# Register User - Duplicate Email
# ==========================================

def test_register_duplicate_email(
    client,
    test_user
):

    data = {
        "name": "Another User",
        "email": "testuser@example.com",
        "password": "password123"
    }

    response = client.post(
        "/register",
        json=data
    )

    assert response.status_code == 409

    response_data = response.get_json()

    assert response_data["error"] == (
        "Email already registered"
    )


# ==========================================
# Register User - Missing Fields
# ==========================================

def test_register_missing_fields(client):

    data = {
        "name": "Adithiya",
        "email": "adithiya@example.com"
    }

    response = client.post(
        "/register",
        json=data
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == (
        "Name, email and password are required"
    )


# ==========================================
# Register User - No Data
# ==========================================

def test_register_no_data(client):

    response = client.post(
        "/register",
        json={}
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == (
        "No data provided"
    )


# ==========================================
# Login User - Success
# ==========================================

def test_login_success(
    client,
    test_user
):

    data = {
        "email": "testuser@example.com",
        "password": "testpassword123"
    }

    response = client.post(
        "/login",
        json=data
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["message"] == (
        "Login successful!"
    )

    assert "access_token" in response_data

    assert response_data["user"]["email"] == (
        "testuser@example.com"
    )

    assert response_data["user"]["name"] == (
        "Test User"
    )


# ==========================================
# Login - Wrong Password
# ==========================================

def test_login_wrong_password(
    client,
    test_user
):

    data = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }

    response = client.post(
        "/login",
        json=data
    )

    assert response.status_code == 401

    response_data = response.get_json()

    assert response_data["error"] == (
        "Invalid email or password"
    )


# ==========================================
# Login - User Not Found
# ==========================================

def test_login_user_not_found(client):

    data = {
        "email": "unknown@example.com",
        "password": "password123"
    }

    response = client.post(
        "/login",
        json=data
    )

    assert response.status_code == 401

    response_data = response.get_json()

    assert response_data["error"] == (
        "Invalid email or password"
    )


# ==========================================
# Login - Missing Fields
# ==========================================

def test_login_missing_fields(client):

    data = {
        "email": "test@example.com"
    }

    response = client.post(
        "/login",
        json=data
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == (
        "Email and password are required"
    )


# ==========================================
# Login - No Data
# ==========================================

def test_login_no_data(client):

    response = client.post(
        "/login",
        json={}
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == (
        "No data provided"
    )


# ==========================================
# Get Profile - Success
# ==========================================

def test_get_profile_success(
    client,
    auth_headers,
    test_user
):

    response = client.get(
        "/profile",
        headers=auth_headers
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["user"]["id"] == test_user.id
    assert response_data["user"]["name"] == test_user.name
    assert response_data["user"]["email"] == test_user.email
    assert response_data["user"]["role"] == test_user.role.value
    assert response_data["user"]["timezone"] == "UTC"
    assert response_data["user"]["webhook_url"] is None


# ==========================================
# Get Profile - Unauthorized
# ==========================================

def test_get_profile_unauthorized(client):

    response = client.get("/profile")

    assert response.status_code == 401


# ==========================================
# Update Profile - Success
# ==========================================

def test_update_profile_success(
    client,
    auth_headers,
    test_user
):

    data = {
        "name": "Updated Name",
        "timezone": "America/New_York",
        "webhook_url": "https://hooks.slack.com/services/TEST"
    }

    response = client.put(
        "/profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["user"]["name"] == "Updated Name"
    assert response_data["user"]["timezone"] == "America/New_York"
    assert response_data["user"]["webhook_url"] == "https://hooks.slack.com/services/TEST"


# ==========================================
# Update Profile - Invalid Timezone
# ==========================================

def test_update_profile_invalid_timezone(
    client,
    auth_headers,
    test_user
):

    data = {
        "timezone": "Invalid/Timezone"
    }

    response = client.put(
        "/profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == "Invalid timezone"


# ==========================================
# Update Profile - Invalid Webhook URL
# ==========================================

def test_update_profile_invalid_webhook(
    client,
    auth_headers,
    test_user
):

    data = {
        "webhook_url": "not-a-valid-url"
    }

    response = client.put(
        "/profile",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == "Invalid webhook URL format"


# ==========================================
# Update Profile - Unauthorized
# ==========================================

def test_update_profile_unauthorized(client):

    response = client.put("/profile", json={"name": "Test"})

    assert response.status_code == 401


# ==========================================
# Change Password - Success
# ==========================================

def test_change_password_success(
    client,
    auth_headers,
    test_user
):

    data = {
        "current_password": "testpassword123",
        "new_password": "newpassword123"
    }

    response = client.put(
        "/password",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["message"] == "Password changed successfully!"


# ==========================================
# Change Password - Wrong Current Password
# ==========================================

def test_change_password_wrong_current(
    client,
    auth_headers,
    test_user
):

    data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }

    response = client.put(
        "/password",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 401

    response_data = response.get_json()

    assert response_data["error"] == "Current password is incorrect"


# ==========================================
# Change Password - Missing Fields
# ==========================================

def test_change_password_missing_fields(
    client,
    auth_headers
):

    data = {
        "current_password": "testpassword123"
    }

    response = client.put(
        "/password",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == "Current password and new password are required"


# ==========================================
# Change Password - Unauthorized
# ==========================================

def test_change_password_unauthorized(client):

    response = client.put("/password", json={"current_password": "a", "new_password": "b"})

    assert response.status_code == 401


# ==========================================
# Delete Account - Success
# ==========================================

def test_delete_account_success(
    client,
    auth_headers,
    test_user
):

    data = {
        "password": "testpassword123"
    }

    response = client.delete(
        "/account",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["message"] == "Account deleted successfully!"

    # Verify user is deleted
    response2 = client.get("/profile", headers=auth_headers)
    assert response2.status_code == 404


# ==========================================
# Delete Account - Wrong Password
# ==========================================

def test_delete_account_wrong_password(
    client,
    auth_headers,
    test_user
):

    data = {
        "password": "wrongpassword"
    }

    response = client.delete(
        "/account",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 401

    response_data = response.get_json()

    assert response_data["error"] == "Password is incorrect"


# ==========================================
# Delete Account - Missing Password
# ==========================================

def test_delete_account_missing_password(
    client,
    auth_headers
):

    data = {}

    response = client.delete(
        "/account",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert response_data["error"] == "Password confirmation required"


# ==========================================
# Delete Account - Unauthorized
# ==========================================

def test_delete_account_unauthorized(client):

    response = client.delete("/account", json={"password": "test"})

    assert response.status_code == 401