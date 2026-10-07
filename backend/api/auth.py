from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity
)

from extensions import db, bcrypt
from models.user import User, Role
from models.token_blocklist import TokenBlocklist
import re


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

    # Allow role specification for HR registration (must be validated by admin in prod)
    role = Role.USER
    if data.get("role") in ("HR", "ADMIN"):
        # Only allow role escalation if there is a valid admin token
        # For simplicity, HR accounts should be created by admin
        role = Role.USER  # Default to USER for self-registration

    user = User(
        name=data["name"],
        email=data["email"],
        password=hashed_password,
        role=role
    )

    db.session.add(user)
    db.session.commit()

    # Create Access + Refresh Tokens (same as login)
    additional_claims = {"role": user.role.value}

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        "message": "User registered successfully!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }
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
    if not user.is_active:
        return jsonify({
            "error": "This account has been disabled. Contact an administrator."
        }), 403

    # =========================
    # Create Access + Refresh Tokens
    # Include role in JWT claims so it can be read without DB lookup
    # =========================
    additional_claims = {"role": user.role.value}

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
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

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    additional_claims = {"role": user.role.value}

    new_access_token = create_access_token(
        identity=str(user_id),
        additional_claims=additional_claims
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


# =========================
# Get Current User Profile
# GET /profile
# =========================
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "timezone": user.timezone,
            "webhook_url": user.webhook_url
        }
    }), 200


# =========================
# Update User Profile
# PUT /profile
# =========================
@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update name if provided
    if "name" in data:
        user.name = data["name"]

    # Update timezone if provided (validate IANA timezone)
    if "timezone" in data:
        timezone = data["timezone"]
        # Basic validation - IANA timezones are typically in format Area/Location
        if timezone:
            try:
                import zoneinfo
                zoneinfo.ZoneInfo(timezone)
                user.timezone = timezone
            except Exception:
                return jsonify({"error": "Invalid timezone"}), 400

    # Update webhook_url if provided (validate URL format)
    if "webhook_url" in data:
        webhook_url = data["webhook_url"]
        if webhook_url:
            # Basic URL validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(webhook_url):
                return jsonify({"error": "Invalid webhook URL format"}), 400
        user.webhook_url = webhook_url

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully!",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "timezone": user.timezone,
            "webhook_url": user.webhook_url
        }
    }), 200


# =========================
# Change Password
# PUT /password
# =========================
@auth_bp.route("/password", methods=["PUT"])
@jwt_required()
def change_password():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "current_password" not in data or "new_password" not in data:
        return jsonify({"error": "Current password and new password are required"}), 400

    # Verify current password
    if not bcrypt.check_password_hash(user.password, data["current_password"]):
        return jsonify({"error": "Current password is incorrect"}), 401

    # Hash new password
    hashed_password = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")
    user.password = hashed_password

    db.session.commit()

    return jsonify({
        "message": "Password changed successfully!"
    }), 200


# =========================
# Delete Account
# DELETE /account
# =========================
@auth_bp.route("/account", methods=["DELETE"])
@jwt_required()
def delete_account():

    user_id = get_jwt_identity()

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data or "password" not in data:
        return jsonify({"error": "Password confirmation required"}), 400

    # Verify password
    if not bcrypt.check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Password is incorrect"}), 401

    # Delete user (cascades to applications, tokens, etc. via model relationships)
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": "Account deleted successfully!"
    }), 200