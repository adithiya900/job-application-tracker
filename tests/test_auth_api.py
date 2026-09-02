import pytest

from app import app
from extensions import db, bcrypt
from models.user import User


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

    assert response_data["name"] == "Adithiya"

    assert response_data["email"] == (
        "adithiya@example.com"
    )

    assert "id" in response_data


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