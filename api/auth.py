from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from extensions import db, bcrypt
from models.user import User


auth_bp = Blueprint("auth", __name__)


# =========================
# Register User
# =========================
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    # Check required fields
    if (
        "name" not in data
        or "email" not in data
        or "password" not in data
    ):
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    # Check existing user
    existing_user = User.query.filter_by(
        email=data["email"]
    ).first()

    if existing_user:
        return jsonify({
            "error": "Email already registered"
        }), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(
        data["password"]
    ).decode("utf-8")

    # Create user
    user = User(
        name=data["name"],
        email=data["email"],
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully!",
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 201


# =========================
# Login User
# =========================
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    # Check required fields
    if "email" not in data or "password" not in data:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    # Find user
    user = User.query.filter_by(
        email=data["email"]
    ).first()

    # Check email and password
    if not user or not bcrypt.check_password_hash(
        user.password,
        data["password"]
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # Create JWT token
    access_token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        "message": "Login successful!",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200