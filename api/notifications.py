from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.digest_service import send_weekly_digest


notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route(
    "/notifications/weekly-digest",
    methods=["POST"]
)
@jwt_required()
def trigger_weekly_digest():
    user_id = int(get_jwt_identity())

    if not send_weekly_digest(user_id):
        return jsonify({
            "error": "Weekly digest could not be sent"
        }), 502

    return jsonify({
        "message": "Weekly digest sent successfully"
    }), 200
