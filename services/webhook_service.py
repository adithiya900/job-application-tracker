import hashlib
import hmac
import json
import logging
import os

import requests


logger = logging.getLogger(__name__)


class WebhookService:

    @staticmethod
    def send_status_change(application, old_status, new_status):
        webhook_url = os.getenv("WEBHOOK_URL")
        webhook_secret = os.getenv("WEBHOOK_SECRET")

        if not webhook_url:
            logger.warning("WEBHOOK_URL is not configured")
            return False

        payload = {
            "event": "application.status_changed",
            "application_id": application.id,
            "user_id": application.user_id,
            "company": application.company,
            "role": application.role,
            "old_status": old_status.value,
            "new_status": new_status.value,
        }

        payload_json = json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True
        )

        signature = hmac.new(
            webhook_secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        }

        for attempt in range(1, 4):
            try:
                response = requests.post(
                    webhook_url,
                    data=payload_json,
                    headers=headers,
                    timeout=10
                )

                response.raise_for_status()

                logger.info(
                    "Webhook sent successfully for application %s "
                    "on attempt %s",
                    application.id,
                    attempt
                )

                return True

            except requests.RequestException as exc:
                logger.error(
                    "Webhook attempt %s failed for application %s: %s",
                    attempt,
                    application.id,
                    exc
                )

        return False

    @staticmethod
    def send_slack_offer_notification(application):
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        if not slack_webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not configured")
            return False

        message = {
            "text": (
                "🎉 Job Application Status Update\n\n"
                f"Company: {application.company}\n"
                f"Role: {application.role}\n"
                "New Status: OFFER\n"
                f"Application ID: {application.id}"
            )
        }

        try:
            response = requests.post(
                slack_webhook_url,
                json=message,
                timeout=10
            )

            response.raise_for_status()

            logger.info(
                "Slack OFFER notification sent for application %s",
                application.id
            )

            return True

        except requests.RequestException as exc:
            logger.error(
                "Slack notification failed for application %s: %s",
                application.id,
                exc
            )
            return False