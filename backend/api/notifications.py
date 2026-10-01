from flask import Blueprint, Response, jsonify, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.digest_service import send_weekly_digest
from services.notification_service import subscribe_to_notifications


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


@notifications_bp.route(
    "/notifications/stream",
    methods=["GET"]
)
@jwt_required()
def notification_stream():

    user_id = str(get_jwt_identity())
    pubsub = subscribe_to_notifications()

    @stream_with_context
    def generate():

        try:

            # Tell the browser that the connection is active.
            yield "event: connected\n"
            yield "data: {\"message\": \"Notification stream connected\"}\n\n"

            while True:

                message = pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=15
                )

                if message is None:
                    # Keep the SSE connection alive.
                    yield ": heartbeat\n\n"
                    continue

                if message["type"] != "message":
                    continue

                event_data = message["data"]

                import json

                event = json.loads(event_data)

                # Only send notifications belonging
                # to the logged-in user.
                if event.get("user_id") != user_id:
                    continue

                yield "event: notification\n"
                yield f"data: {event_data}\n\n"

        finally:
            pubsub.close()

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )