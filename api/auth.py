from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity
)

from extensions import db, bcrypt
from models.user import User
from models.token_blocklist import TokenBlocklist


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

    if (
        "name" not in data
        or "email" not in data
        or "password" not in data
    ):
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    existing_user = User.query.filter_by(
        email=data["email"]
    ).first()

    if existing_user:
        return jsonify({
            "error": "Email already registered"
        }), 409

    hashed_password = bcrypt.generate_password_hash(
        data["password"]
    ).decode("utf-8")

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

    if "email" not in data or "password" not in data:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.query.filter_by(
        email=data["email"]
    ).first()

    if not user or not bcrypt.check_password_hash(
        user.password,
        data["password"]
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # =========================
    # Create Access + Refresh Tokens
    # =========================
    access_token = create_access_token(
        identity=str(user.id)
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return jsonify({
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "name": user.name
        }
    }), 200


# =========================
# Refresh Access Token
# POST /refresh
# =========================
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    user_id = get_jwt_identity()

    new_access_token = create_access_token(
        identity=str(user_id)
    )

    return jsonify({
        "message": "Access token refreshed successfully!",
        "access_token": new_access_token
    }), 200


# =========================
# Logout User
# POST /logout
# =========================
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    jwt_data = get_jwt()

    jti = jwt_data["jti"]
    token_type = jwt_data.get("type", "access")
    user_id = int(get_jwt_identity())

    # Check whether token is already blacklisted
    existing_token = TokenBlocklist.query.filter_by(
        jti=jti
    ).first()

    if existing_token:
        return jsonify({
            "message": "Token already revoked"
        }), 200

    revoked_token = TokenBlocklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id
    )

    db.session.add(revoked_token)
    db.session.commit()

    return jsonify({
        "message": "Logout successful! Token revoked."
    }), 200