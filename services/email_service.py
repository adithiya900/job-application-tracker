from flask_mail import Message
from flask import render_template
from extensions import mail


def send_email(subject, recipients, body, html=None):
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html
        )

        mail.send(msg)

        return True

    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def send_template_email(
    subject,
    recipients,
    template_name,
    template_context,
    body
):
    html = render_template(
        template_name,
        **template_context
    )

    return send_email(
        subject=subject,
        recipients=recipients,
        body=body,
        html=html
    )