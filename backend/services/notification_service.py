import json
import os

import redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

NOTIFICATION_CHANNEL = "job_tracker_notifications"


def get_redis_client():
    """Create and return a Redis client."""
    return redis.from_url(
        REDIS_URL,
        decode_responses=True
    )


def publish_notification(
    user_id,
    notification_type,
    message,
    data=None
):
    """
    Publish a notification event to Redis Pub/Sub.

    The user_id allows the frontend/SSE layer to identify
    which user should receive the notification.
    """

    event = {
        "user_id": str(user_id),
        "type": notification_type,
        "message": message,
        "data": data or {}
    }

    client = get_redis_client()

    client.publish(
        NOTIFICATION_CHANNEL,
        json.dumps(event)
    )


def subscribe_to_notifications():
    """
    Subscribe to the application notification channel.

    Used by the SSE endpoint to receive real-time events.
    """

    client = get_redis_client()

    pubsub = client.pubsub()
    pubsub.subscribe(NOTIFICATION_CHANNEL)

    return pubsub