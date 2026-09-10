from flask import Blueprint, jsonify

from flask_jwt_extended import (
    get_jwt_identity,
    create_access_token
)

from models.user import User
from utils.admin import admin_required


admin_bp = Blueprint("admin", __name__)


# ==========================================
# Admin - List All Users
# GET /api/admin/users
# ==========================================

@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def list_users():

    current_user_id = int(get_jwt_identity())

    users = User.query.order_by(User.id).all()

    result = []

    for user in users:
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "is_current_user": user.id == current_user_id
        })

    return jsonify({
        "users": result,
        "count": len(result)
    }), 200


# ==========================================
# Admin - Impersonate User
# POST /api/admin/users/<user_id>/impersonate
# ==========================================

@admin_bp.route(
    "/api/admin/users/<int:user_id>/impersonate",
    methods=["POST"]
)
@admin_required
def impersonate_user(user_id):

    current_admin_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    if user.id == current_admin_id:
        return jsonify({
            "error": "Admin cannot impersonate themselves"
        }), 400

    impersonation_token = create_access_token(
        identity=str(user.id),
        additional_claims={"impersonated_by": current_admin_id}
    )

    return jsonify({
        "message": "User impersonation token created",
        "impersonated_user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        },
        "access_token": impersonation_token
    }), 200
