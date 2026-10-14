import hashlib
import hmac
import json

import requests

from services.webhook_service import WebhookService


def test_webhook_hmac_signature(monkeypatch):
    monkeypatch.setenv(
        "WEBHOOK_URL",
        "https://example.com/webhook"
    )
    monkeypatch.setenv(
        "WEBHOOK_SECRET",
        "test-secret"
    )

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    def fake_post(url, data, headers, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "services.webhook_service.requests.post",
        fake_post
    )

    class FakeApplication:
        id = 10
        user_id = 2
        company = "Google"
        role = "Software Engineer"

    class FakeStatus:
        def __init__(self, value):
            self.value = value

    old_status = FakeStatus("INTERVIEW")
    new_status = FakeStatus("OFFER")

    result = WebhookService.send_status_change(
        FakeApplication(),
        old_status,
        new_status
    )

    assert result is True
    assert captured["url"] == "https://example.com/webhook"

    expected_payload = {
        "event": "application.status_changed",
        "application_id": 10,
        "user_id": 2,
        "company": "Google",
        "role": "Software Engineer",
        "old_status": "INTERVIEW",
        "new_status": "OFFER",
    }

    expected_json = json.dumps(
        expected_payload,
        separators=(",", ":"),
        sort_keys=True
    )

    expected_signature = hmac.new(
        b"test-secret",
        expected_json.encode(),
        hashlib.sha256
    ).hexdigest()

    assert (
        captured["headers"]["X-Webhook-Signature"]
        == expected_signature
    )


def test_webhook_retries_three_times(monkeypatch):
    monkeypatch.setenv(
        "WEBHOOK_URL",
        "https://example.com/webhook"
    )
    monkeypatch.setenv(
        "WEBHOOK_SECRET",
        "test-secret"
    )

    attempts = []

    def fake_post(url, data, headers, timeout):
        attempts.append(1)
        raise requests.RequestException("Webhook failed")

    monkeypatch.setattr(
        "services.webhook_service.requests.post",
        fake_post
    )

    class FakeApplication:
        id = 10
        user_id = 2
        company = "Google"
        role = "Software Engineer"

    class FakeStatus:
        def __init__(self, value):
            self.value = value

    old_status = FakeStatus("INTERVIEW")
    new_status = FakeStatus("OFFER")

    result = WebhookService.send_status_change(
        FakeApplication(),
        old_status,
        new_status
    )

    assert result is False
    assert len(attempts) == 3


def test_slack_offer_notification_has_been_removed(monkeypatch):
    """The Slack integration must be gone, not merely unconfigured."""
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")
    assert not hasattr(WebhookService, "send_slack_offer_notification")


def test_status_change_ignores_slack_environment(monkeypatch):
    """The generic webhook must not read SLACK_WEBHOOK_URL."""
    import os
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")

    class FakeApplication:
        id = 1
        user_id = 1
        company = "Acme"
        role = "Engineer"

    class FakeStatus:
        def __init__(self, value):
            self.value = value

    assert WebhookService.send_status_change(
        FakeApplication(),
        FakeStatus("APPLIED"),
        FakeStatus("OFFER"),
    ) is False
    assert "SLACK_WEBHOOK_URL" not in open(
        os.path.join(os.path.dirname(__file__), "..", "services", "webhook_service.py")
    ).read()


def test_status_change_still_fires_after_application_update(test_app, test_user, test_application, monkeypatch):
    """
    Regression: moving an application to OFFER must still fire the generic
    status-change webhook and must NOT attempt any Slack delivery.
    """
    from unittest.mock import patch
    from models.job import ApplicationStatus
    from services.application_service import ApplicationService

    with patch.object(
        WebhookService, "send_status_change", return_value=True
    ) as status_hook, patch(
        "services.webhook_service.requests.post"
    ) as post:
        monkeypatch.delenv("WEBHOOK_URL", raising=False)
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")

        ApplicationService.update_application(
            test_application.id,
            {"status": ApplicationStatus.OFFER},
            test_user.id,
        )

    status_hook.assert_called_once()
    assert status_hook.call_args.kwargs["new_status"] == ApplicationStatus.OFFER
    assert status_hook.call_args.kwargs["old_status"] == ApplicationStatus.APPLIED

    # No outbound HTTP call of any kind: Slack is gone and WEBHOOK_URL is unset.
    post.assert_not_called()


def test_no_network_call_is_made_for_offer_status(monkeypatch):
    """An OFFER status change must not open an outbound Slack connection."""
    calls = []

    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")

    def fake_post(*args, **kwargs):
        calls.append(args[0] if args else kwargs.get("url"))
        raise AssertionError("No outbound webhook call is expected without WEBHOOK_URL")

    monkeypatch.setattr("services.webhook_service.requests.post", fake_post)

    class FakeApplication:
        id = 5
        user_id = 3
        company = "Initech"
        role = "Dev"

    class FakeStatus:
        def __init__(self, value):
            self.value = value

    WebhookService.send_status_change(
        FakeApplication(),
        FakeStatus("APPLIED"),
        FakeStatus("OFFER"),
    )

    assert calls == []