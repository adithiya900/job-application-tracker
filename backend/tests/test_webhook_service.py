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