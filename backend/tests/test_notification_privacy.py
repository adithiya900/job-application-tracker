"""
Notification privacy / recipient-isolation tests.

Notifications are delivered over Redis Pub/Sub and an SSE stream. These tests
prove that a private notification addressed to one candidate is never delivered
to another candidate, and that every notification-retrieval API filters by the
authenticated owner.
"""

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from extensions import db
from models.user import User, Role
from models.job import JobApplication
from models.reminder import FollowUpReminder, ReminderStatus, ReminderType
from tests.factories import UserFactory, ApplicationFactory


class FakePubSub:
    """
    Stand-in for a Redis pub/sub connection.

    `messages` is a flat list of every event published on the shared channel,
    exactly like what the real channel receives from all users.
    """

    def __init__(self, messages):
        self._messages = list(messages)

    def subscribe(self, channel):
        pass

    def get_message(self, ignore_subscribe_messages=True, timeout=0):
        if self._messages:
            return {"type": "message", "data": self._messages.pop(0)}
        return None

    def close(self):
        pass


def _token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role.value},
    )


def _headers(user):
    return {"Authorization": f"Bearer {_token(user)}"}


def _event(user_id, text):
    return json.dumps({
        "user_id": str(user_id),
        "type": "HR_MESSAGE",
        "message": text,
        "data": {},
    })


@pytest.fixture
def two_candidates():
    first = UserFactory(role=Role.USER, email="cand-a@example.com")
    second = UserFactory(role=Role.USER, email="cand-b@example.com")
    ApplicationFactory(user=first)
    ApplicationFactory(user=second)
    return first, second


def _read_stream(client, headers, messages, query_string=None):
    """
    Drain one SSE response to completion.

    The stream is bounded by patching its max lifetime so the test cannot hang
    on the heartbeat loop; the fake pubsub hands back every published message.
    """
    fake = FakePubSub(messages)
    with patch(
        "api.notifications.subscribe_to_notifications",
        return_value=fake,
    ), patch("api.notifications.SSE_MAX_LIFETIME_SECONDS", 1):
        response = client.get(
            "/notifications/stream",
            query_string=query_string,
            headers={**headers, "Accept": "text/event-stream"},
        )
        assert response.status_code == 200
        body = b"".join(response.iter_encoded()).decode("utf-8")
    return body


def _received_messages(stream_body):
    """Extract the message payloads of real 'notification' events only."""
    messages = []
    for block in stream_body.split("\n\n"):
        if "event: notification" not in block:
            continue
        for line in block.splitlines():
            if line.startswith("data: "):
                messages.append(json.loads(line[len("data: "):]))
    return messages


# ==========================================================================
# Real-time delivery isolation
# ==========================================================================

def test_sse_stream_delivers_only_the_authenticated_users_notifications(client, two_candidates):
    candidate_a, candidate_b = two_candidates

    stream = _read_stream(
        client,
        _headers(candidate_a),
        [
            _event(candidate_b.id, "PRIVATE-FOR-B"),
            _event(candidate_a.id, "FOR-A"),
            _event(999999, "for-somebody-else"),
        ],
    )

    received = _received_messages(stream)
    messages = [item["message"] for item in received]

    assert "FOR-A" in messages
    assert "PRIVATE-FOR-B" not in messages
    assert "for-somebody-else" not in messages

    # The other candidate's payload must not appear anywhere in the stream.
    assert "PRIVATE-FOR-B" not in stream


def test_each_candidate_sees_only_their_own_events(client, two_candidates):
    candidate_a, candidate_b = two_candidates
    events = [
        _event(candidate_a.id, "A1"),
        _event(candidate_b.id, "B1"),
        _event(candidate_a.id, "A2"),
        _event(candidate_b.id, "B2"),
    ]

    stream_a = _read_stream(client, _headers(candidate_a), list(events))
    stream_b = _read_stream(client, _headers(candidate_b), list(events))

    assert [item["message"] for item in _received_messages(stream_a)] == ["A1", "A2"]
    assert [item["message"] for item in _received_messages(stream_b)] == ["B1", "B2"]
    assert "B1" not in stream_a
    assert "A1" not in stream_b


def test_sse_stream_requires_authentication(client):
    with patch("api.notifications.SSE_MAX_LIFETIME_SECONDS", 1):
        assert client.get("/notifications/stream").status_code == 401


def test_sse_identity_cannot_be_overridden_by_parameters(client, two_candidates):
    """Guessing or changing ids/params must not expose someone else's events."""
    candidate_a, candidate_b = two_candidates

    stream = _read_stream(
        client,
        _headers(candidate_a),
        [_event(candidate_b.id, "PRIVATE-FOR-B"), _event(candidate_a.id, "FOR-A")],
        query_string={"user_id": candidate_b.id},
    )

    received = [item["message"] for item in _received_messages(stream)]
    assert "FOR-A" in received
    # The JWT identity decides the recipient, not the query string.
    assert "PRIVATE-FOR-B" not in received
    assert "PRIVATE-FOR-B" not in stream


# ==========================================================================
# Persisted notification/reminder endpoints
# ==========================================================================

def _reminder(user, application, message, day):
    return FollowUpReminder(
        application_id=application.id,
        user_id=user.id,
        reminder_type=ReminderType.FOLLOW_UP,
        message=message,
        scheduled_at=datetime(2026, 12, day, 9, 0, 0),
        status=ReminderStatus.PENDING,
    )


def test_candidate_reminders_are_scoped_to_the_owner(client, two_candidates):
    candidate_a, candidate_b = two_candidates
    app_a = ApplicationFactory(user=candidate_a)
    app_b = ApplicationFactory(user=candidate_b)

    db.session.add_all((
        _reminder(candidate_a, app_a, "A-only reminder", 1),
        _reminder(candidate_b, app_b, "B-private reminder", 2),
    ))
    db.session.commit()

    response = client.get("/api/reminders", headers=_headers(candidate_a))
    assert response.status_code == 200

    payload = response.get_json()
    messages = [item.get("message") for item in payload.get("reminders", [])]
    assert "A-only reminder" in messages
    assert "B-private reminder" not in messages


def test_candidate_cannot_dismiss_another_candidates_reminder(client, two_candidates):
    candidate_a, candidate_b = two_candidates
    app_b = ApplicationFactory(user=candidate_b)
    reminder = _reminder(candidate_b, app_b, "B-private reminder", 2)
    db.session.add(reminder)
    db.session.commit()

    forbidden = client.patch(
        f"/api/reminders/{reminder.id}/dismiss",
        headers=_headers(candidate_a),
    )
    assert forbidden.status_code == 404

    db.session.refresh(reminder)
    assert reminder.dismissed is False


def test_candidate_cannot_read_another_candidates_application(client, two_candidates):
    candidate_a, candidate_b = two_candidates
    app_b = ApplicationFactory(user=candidate_b, company="PrivateCo")

    forbidden = client.get(
        f"/api/applications/{app_b.id}",
        headers=_headers(candidate_a),
    )
    assert forbidden.status_code in (403, 404)


def test_candidate_cannot_download_another_candidates_resume(client, two_candidates):
    candidate_a, candidate_b = two_candidates

    app_b = ApplicationFactory(user=candidate_b, resume_path="someone-elses-resume.pdf")
    forbidden = client.get(
        f"/files/{app_b.resume_path.rsplit('/', 1)[-1]}",
        headers=_headers(candidate_a),
    )
    assert forbidden.status_code == 404


# ==========================================================================
# Sender-side correctness
# ==========================================================================

def test_hr_notification_is_published_to_the_named_recipient(client):
    hr = UserFactory(role=Role.ADMIN, email="hr-sender@example.com")
    candidate = UserFactory(role=Role.USER, email="recipient@example.com")
    other = UserFactory(role=Role.USER, email="bystander@example.com")
    application = ApplicationFactory(user=candidate)

    published = {}

    def _capture(**kwargs):
        published.update(kwargs)

    with patch("api.hr.publish_notification", side_effect=_capture):
        response = client.post(
            f"/api/hr/applications/{application.id}/notify",
            json={"message": "Your interview is confirmed."},
            headers=_headers(hr),
        )

    assert response.status_code == 200
    # The recipient is the owning candidate, never a broadcast.
    assert published["user_id"] == candidate.id
    assert published["user_id"] != other.id


def test_hr_notification_is_refused_for_unknown_application(client):
    hr = UserFactory(role=Role.ADMIN, email="hr-sender2@example.com")
    response = client.post(
        "/api/hr/applications/999999/notify",
        json={"message": "Hello?"},
        headers=_headers(hr),
    )
    assert response.status_code == 404


def test_candidate_cannot_send_hr_notifications(client):
    candidate = UserFactory(role=Role.USER, email="impersonator@example.com")
    application = ApplicationFactory(user=candidate)
    response = client.post(
        f"/api/hr/applications/{application.id}/notify",
        json={"message": "promoting myself"},
        headers=_headers(candidate),
    )
    assert response.status_code == 403


def test_hr_cannot_notify_when_candidate_is_disabled(client):
    """Existing business rule: disabled candidates receive no HR notifications."""
    hr = UserFactory(role=Role.ADMIN, email="hr-disabled@example.com")
    candidate = UserFactory(role=Role.USER, email="offlined@example.com", is_active=False)
    application = ApplicationFactory(user=candidate)

    with patch("api.hr.publish_notification") as publisher:
        response = client.post(
            f"/api/hr/applications/{application.id}/notify",
            json={"message": "still there?"},
            headers=_headers(hr),
        )
    assert response.status_code == 403
    publisher.assert_not_called()
