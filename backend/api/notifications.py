from flask import Blueprint, Response, jsonify, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required
import json
import os
import time

from services.digest_service import send_weekly_digest
from services.notification_service import subscribe_to_notifications


notifications_bp = Blueprint("notifications", __name__)

# Bound how long one SSE connection may stay open. The browser's EventSource
# reconnects when the stream ends, so this keeps a stalled or forgotten stream
# from tying up a gunicorn worker thread indefinitely.
SSE_MAX_LIFETIME_SECONDS = int(os.getenv("SSE_MAX_LIFETIME_SECONDS", "300"))

# How long to block waiting for a Redis message before emitting a heartbeat.
# A short interval keeps the client alive but, more importantly, makes the
# worker attempt a write (and so notice a dropped client) quickly instead of
# holding its thread for the whole stale-stream window.
SSE_POLL_SECONDS = float(os.getenv("SSE_POLL_SECONDS", "2"))


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

        started_at = time.monotonic()

        try:

            # Tell the browser that the connection is active.
            yield "event: connected\n"
            yield "data: {\"message\": \"Notification stream connected\"}\n\n"

            while True:

                if time.monotonic() - started_at > SSE_MAX_LIFETIME_SECONDS:
                    # Close the stream; the client reconnects and picks it up.
                    yield "event: reconnect\n"
                    yield "data: {\"message\": \"Stream expired, reconnecting\"}\n\n"
                    return

                message = pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=SSE_POLL_SECONDS
                )

                if message is None:
                    # Keep the SSE connection alive.
                    yield ": heartbeat\n\n"
                    continue

                if message["type"] != "message":
                    continue

                event_data = message["data"]

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
        # "close" (not "keep-alive"): an SSE socket must never be returned to
        # the browser's shared connection pool for reuse. Pooling it means a
        # few hard refreshes exhaust the per-host socket limit and every later
        # navigation stalls.
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "close"
        }
    )